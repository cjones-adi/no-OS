#!/bin/bash

# framework_validation.sh - Framework validation script for no-OS driver development
# MANDATORY before ANY driver implementation

set -e  # Exit on error

DEVICE_NAME="${1:-}"
DEVICE_CATEGORY="${2:-}"
PLATFORM="${3:-maxim}"

if [[ -z "$DEVICE_NAME" ]]; then
    echo "Usage: $0 <device_name> [category] [platform]"
    echo "Example: $0 ltm4700 power maxim"
    exit 1
fi

echo "🔍 Framework Validation for $DEVICE_NAME ($DEVICE_CATEGORY, $PLATFORM platform)"
echo "========================================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VALIDATION_FAILED=0

# Helper function for validation results
validate_check() {
    local description="$1"
    local command="$2"

    echo -n "Checking $description... "

    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        VALIDATION_FAILED=1
        return 1
    fi
}

echo ""
echo "📁 1. Build System Pattern Validation"
echo "------------------------------------"

# Check for reference src.mk files
validate_check "reference src.mk files" "test -f \$(find projects/ -name 'src.mk' | head -1)"

# Validate include patterns (no wildcards)
if find projects/ -name "src.mk" -exec grep -l "\*\*" {} \; | head -1 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  WARNING: Found wildcard includes in existing projects${NC}"
    echo "   Projects with wildcards should be avoided in new implementations"
fi

# Check examples.mk integration pattern
SAMPLE_PROJECT=$(find projects/ -name "src.mk" | head -1)
if [[ -f "$SAMPLE_PROJECT" ]]; then
    if grep -q "examples.mk" "$SAMPLE_PROJECT"; then
        echo -e "   ${GREEN}✓ Examples integration pattern found${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Examples integration pattern not found in sample${NC}"
    fi
fi

echo ""
echo "🔌 2. Platform API Validation"
echo "-----------------------------"

case "$PLATFORM" in
    "maxim")
        # Maxim headers are chip-specific, find any available implementation
        validate_check "maxim_uart.h header" "find drivers/platform/maxim/ -name 'maxim_uart.h' | head -1"
        validate_check "maxim_i2c.h header" "find drivers/platform/maxim/ -name 'maxim_i2c.h' | head -1"
        validate_check "maxim_gpio.h header" "find drivers/platform/maxim/ -name 'maxim_gpio.h' | head -1"

        # Check for specific constants in any available chip variant
        MAXIM_UART_HEADER=$(find drivers/platform/maxim/ -name "maxim_uart.h" | head -1)
        if [[ -f "$MAXIM_UART_HEADER" ]]; then
            validate_check "MAX_UART_FLOW_DIS constant" "grep -q 'MAX_UART_FLOW_DIS' '$MAXIM_UART_HEADER'"
        fi
        ;;
    "stm32")
        validate_check "STM32 platform headers" "test -d drivers/platform/stm32"
        validate_check "STM32 HAL integration" "find drivers/platform/stm32/ -name '*.h' | head -1"
        ;;
    "xilinx")
        validate_check "Xilinx platform headers" "test -d drivers/platform/xilinx"
        ;;
    *)
        echo -e "${YELLOW}⚠️  Platform '$PLATFORM' validation not implemented${NC}"
        ;;
esac

echo ""
echo "🧪 3. Test Framework Validation"
echo "-------------------------------"

# Find a sample test configuration
SAMPLE_TEST=$(find tests/drivers/ -name "project.yml" | head -1)
if [[ -f "$SAMPLE_TEST" ]]; then
    echo "   Using reference: $SAMPLE_TEST"

    # Check Ceedling version
    CEEDLING_VERSION=$(grep "ceedling_version" "$SAMPLE_TEST" | cut -d: -f3 | tr -d ' ' | tr -d '"')
    if [[ "$CEEDLING_VERSION" == "1.0.1" ]]; then
        echo -e "   ${GREEN}✓ Ceedling version: $CEEDLING_VERSION${NC}"
    else
        echo -e "   ${RED}❌ Ceedling version mismatch: $CEEDLING_VERSION (expected 1.0.1)${NC}"
        VALIDATION_FAILED=1
    fi

    # Check modern configuration format
    if grep -q ":use_test_preprocessor:.*:all" "$SAMPLE_TEST"; then
        echo -e "   ${GREEN}✓ Modern preprocessor configuration format${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Legacy test preprocessor format detected${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠️  No reference test configuration found${NC}"
fi

# Check for Unity test patterns
SAMPLE_TEST_SRC=$(find tests/drivers/ -name "test_*.c" | head -1)
if [[ -f "$SAMPLE_TEST_SRC" ]]; then
    validate_check "Unity test include pattern" "grep -q '#include.*unity' '$SAMPLE_TEST_SRC'"
    validate_check "CMock ExpectAndReturn pattern" "grep -q 'ExpectAndReturn' '$SAMPLE_TEST_SRC'"
fi

echo ""
echo "🔧 4. API Signature Validation"
echo "------------------------------"

# Check no-OS core APIs
validate_check "no-OS I2C API" "find include/ drivers/api/ -name '*i2c*' | head -1"
validate_check "no-OS GPIO API" "find include/ drivers/api/ -name '*gpio*' | head -1"

# Check CRC API (common source of implementation errors)
if find include/ drivers/api/ -name "*crc*" | head -1 >/dev/null 2>&1; then
    validate_check "CRC populate function" "grep -r 'no_os_crc8_populate_msb' include/ drivers/api/"
    echo -e "   ${GREEN}✓ CRC API signatures validated${NC}"
else
    echo -e "   ${YELLOW}⚠️  CRC API not found (may not be needed)${NC}"
fi

# Check IIO API for monitoring devices
if [[ "$DEVICE_CATEGORY" == "power" ]] || [[ "$DEVICE_CATEGORY" == "adc" ]]; then
    validate_check "IIO core API" "test -f iio/iio.h || test -f include/iio.h"
    # Check for IIO channel structure in iio_types.h
    if [[ -f "iio/iio_types.h" ]]; then
        validate_check "IIO channel structure" "grep -q 'ch_num' 'iio/iio_types.h'"
        echo -e "   ${GREEN}✓ IIO structure field names validated${NC}"
    elif find . -name "iio.h" | head -1 >/dev/null 2>&1; then
        IIO_HEADER=$(find . -name "iio.h" | head -1)
        validate_check "IIO channel structure" "grep -q 'ch_num' '$IIO_HEADER'"
        echo -e "   ${GREEN}✓ IIO structure field names validated${NC}"
    fi
fi

echo ""
echo "📝 5. Reference Driver Analysis"
echo "------------------------------"

# Find similar drivers for reference
if [[ -n "$DEVICE_CATEGORY" ]]; then
    REFERENCE_DRIVERS=$(find drivers/$DEVICE_CATEGORY/ -maxdepth 1 -type d | grep -v "^drivers/$DEVICE_CATEGORY/$" | head -3)
    if [[ -n "$REFERENCE_DRIVERS" ]]; then
        echo "   Reference drivers found:"
        echo "$REFERENCE_DRIVERS" | while read -r driver; do
            driver_name=$(basename "$driver")
            echo "     - $driver_name"

            # Check for common patterns
            if [[ -f "$driver/${driver_name}.h" ]]; then
                echo -e "       ${GREEN}✓ Standard header structure${NC}"
            fi
            if [[ -f "$driver/iio_${driver_name}.h" ]]; then
                echo -e "       ${GREEN}✓ IIO integration present${NC}"
            fi
        done
    else
        echo -e "   ${YELLOW}⚠️  No reference drivers found in $DEVICE_CATEGORY${NC}"
    fi
fi

echo ""
echo "========================================================================"

if [[ $VALIDATION_FAILED -eq 0 ]]; then
    echo -e "${GREEN}🎉 Framework Validation PASSED${NC}"
    echo "   Safe to proceed with driver implementation planning"
    echo ""
    echo "Next steps:"
    echo "   1. Use EnterPlanMode for comprehensive planning"
    echo "   2. Follow 6-commit implementation pattern"
    echo "   3. Use verified API patterns and build configurations"
    exit 0
else
    echo -e "${RED}💥 Framework Validation FAILED${NC}"
    echo "   Fix framework issues before proceeding with implementation"
    echo ""
    echo "🔧 Quick fixes:"
    echo "   - Platform headers: Check chip-specific directories (max32665/, max32650/)"
    echo "   - Ceedling version: Verify YAML field parsing in project.yml"
    echo "   - IIO structures: Check iio_types.h for ch_num field"
    echo "   - Platform config: Include common directory and DMA sources"
    echo ""
    echo "📖 Detailed troubleshooting:"
    echo "   docs/framework-validation-troubleshooting.md"
    echo "   docs/framework-validation-lessons.md"
    exit 1
fi