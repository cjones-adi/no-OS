#!/usr/bin/env python3
"""
Webhook server for real-time pattern updates.
Listens for GitHub PR events and updates patterns immediately.
"""

import json
import hashlib
import hmac
from flask import Flask, request, jsonify
from pathlib import Path
import subprocess
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Configuration
WEBHOOK_SECRET = None  # Set via environment variable: GITHUB_WEBHOOK_SECRET
REPO_ROOT = Path(__file__).parent.parent.parent
PATTERNS_FILE = REPO_ROOT / "review_patterns_6month.json"

class WebhookPatternUpdater:
    def __init__(self):
        self.update_queue = []
        self.update_thread = None
        self.is_processing = False

    def verify_signature(self, payload_body, signature_header):
        """Verify GitHub webhook signature."""
        if not WEBHOOK_SECRET:
            return True  # Skip verification in development

        signature = hmac.new(
            WEBHOOK_SECRET.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()

        expected = f"sha256={signature}"
        return hmac.compare_digest(expected, signature_header)

    def queue_pr_update(self, pr_number, action):
        """Queue a PR for pattern analysis."""
        self.update_queue.append({
            'pr_number': pr_number,
            'action': action,
            'timestamp': datetime.now().isoformat()
        })

        # Start processing thread if not already running
        if not self.is_processing:
            self.start_processing()

    def start_processing(self):
        """Start background processing of queued updates."""
        if self.update_thread and self.update_thread.is_alive():
            return

        self.update_thread = threading.Thread(target=self.process_queue)
        self.update_thread.daemon = True
        self.update_thread.start()

    def process_queue(self):
        """Process queued PR updates in background."""
        self.is_processing = True

        while self.update_queue:
            update = self.update_queue.pop(0)
            try:
                print(f"🔄 Processing PR #{update['pr_number']} ({update['action']})")
                self.update_patterns_for_pr(update['pr_number'])
                print(f"✅ Completed PR #{update['pr_number']}")

                # Small delay to avoid overwhelming the system
                time.sleep(2)

            except Exception as e:
                print(f"❌ Error processing PR #{update['pr_number']}: {e}")

        self.is_processing = False

    def update_patterns_for_pr(self, pr_number):
        """Update patterns for a specific PR."""
        # Use the auto-update script
        script_path = REPO_ROOT / "tools/pre-commit/auto-update-patterns.py"

        # Create a temporary script that analyzes just this PR
        temp_script = f"""
import sys
sys.path.append('{script_path.parent}')
from auto_update_patterns import ReviewPatternUpdater

updater = ReviewPatternUpdater()
# Analyze just this PR
comments = updater.analyze_pr_comments({pr_number})
if comments:
    # Load existing patterns and add new comments
    patterns, state = updater.load_existing_patterns()
    if patterns:
        for comment in comments:
            category = comment['category']
            patterns['category_counts'][category] = patterns['category_counts'].get(category, 0) + 1

        # Save updated patterns
        import json
        with open('{PATTERNS_FILE}', 'w') as f:
            json.dump(patterns, f, indent=2)

        print(f"Added {{len(comments)}} comments from PR #{pr_number}")
"""

        # Execute the update
        try:
            result = subprocess.run([
                'python3', '-c', temp_script
            ], cwd=REPO_ROOT, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"📊 Updated patterns: {result.stdout.strip()}")
            else:
                print(f"⚠️ Update warning: {result.stderr}")

        except Exception as e:
            print(f"❌ Failed to update patterns: {e}")

updater = WebhookPatternUpdater()

@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    """Handle GitHub webhook events."""

    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not updater.verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 403

    # Parse payload
    payload = request.get_json()
    if not payload:
        return jsonify({'error': 'Invalid JSON'}), 400

    # Handle different event types
    event_type = request.headers.get('X-GitHub-Event')

    if event_type == 'pull_request':
        # PR opened, closed, synchronized
        action = payload.get('action')
        pr = payload.get('pull_request', {})
        pr_number = pr.get('number')

        if action in ['closed'] and pr.get('merged'):
            # PR was merged - update patterns
            print(f"📝 PR #{pr_number} merged, queuing for analysis...")
            updater.queue_pr_update(pr_number, action)

        return jsonify({'status': 'queued', 'pr': pr_number, 'action': action})

    elif event_type == 'pull_request_review':
        # New review added
        action = payload.get('action')
        pr_number = payload.get('pull_request', {}).get('number')

        if action in ['submitted']:
            print(f"💬 Review added to PR #{pr_number}, queuing for analysis...")
            updater.queue_pr_update(pr_number, 'review_added')

        return jsonify({'status': 'queued', 'pr': pr_number, 'action': action})

    elif event_type == 'pull_request_review_comment':
        # Line comment added
        action = payload.get('action')
        pr_number = payload.get('pull_request', {}).get('number')

        if action in ['created']:
            print(f"📝 Line comment added to PR #{pr_number}, queuing for analysis...")
            updater.queue_pr_update(pr_number, 'comment_added')

        return jsonify({'status': 'queued', 'pr': pr_number, 'action': action})

    return jsonify({'status': 'ignored', 'event': event_type})

@app.route('/status', methods=['GET'])
def status():
    """Check webhook server status."""
    return jsonify({
        'status': 'running',
        'queue_length': len(updater.update_queue),
        'processing': updater.is_processing,
        'patterns_file': str(PATTERNS_FILE),
        'patterns_exists': PATTERNS_FILE.exists()
    })

@app.route('/trigger-update', methods=['POST'])
def trigger_manual_update():
    """Manually trigger a pattern update."""
    try:
        # Run the auto-update script
        result = subprocess.run([
            'python3',
            str(REPO_ROOT / 'tools/pre-commit/auto-update-patterns.py')
        ], cwd=REPO_ROOT, capture_output=True, text=True)

        return jsonify({
            'status': 'completed',
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    import os

    # Load webhook secret from environment
    WEBHOOK_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET')

    if not WEBHOOK_SECRET:
        print("⚠️ No GITHUB_WEBHOOK_SECRET found. Signature verification disabled.")
        print("   Set environment variable for production use.")

    print(f"🚀 Starting webhook server for pattern updates...")
    print(f"📁 Watching: {PATTERNS_FILE}")
    print(f"🔗 Endpoints:")
    print(f"   POST /webhook/github    - GitHub webhooks")
    print(f"   GET  /status           - Server status")
    print(f"   POST /trigger-update   - Manual update")

    # Development server
    app.run(host='0.0.0.0', port=5000, debug=False)