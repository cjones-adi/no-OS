## West Command Reference

### Essential West Commands

**Initialize workspace**:
```bash
west init -l zephyr  # Initialize workspace with local manifest
```

**Update repositories**:
```bash
west update  # Fetch/update all repositories in manifest
```

**Build application**:
```bash
west build -b <board> <source_dir>
```

**Build with pristine**:
```bash
west build -p always -b <board> <source_dir>  # Clean build
west build -p auto -b <board> <source_dir>    # Auto-detect if clean needed
```

**Flash to board**:
```bash
west flash  # Flash binary to connected board
```

**Attach debugger**:
```bash
west debug      # Interactive debugger
west debugserver # Start debug server
```

**List boards**:
```bash
west boards  # Show all supported boards
```

### West Build Options

| Option | Description | Example |
|--------|-------------|---------|
| `-b BOARD` | Specify target board | `west build -b nrf52840dk/nrf52840` |
| `-d BUILD_DIR` | Build directory | `west build -d build_custom` |
| `-p {auto,always,never}` | Pristine build | `west build -p always` |
| `-t TARGET` | Build specific target | `west build -t menuconfig` |
| `--shield SHIELD` | Add shield | `west build --shield adafruit_2_8_tft_touch_v2` |
| `-S SNIPPET` | Add snippet | `west build -S usb-console` |
| `--extra-conf FILE` | Extra config file | `west build --extra-conf debug.conf` |
| `--extra-dtc-overlay FILE` | Extra overlay | `west build --extra-dtc-overlay custom.overlay` |
| `-c` | Force CMake run | `west build -c` |
| `--cmake-only` | Run CMake without building | `west build --cmake-only` |

### Common West Build Patterns

**Basic build**:
```bash
cd zephyrproject
source .venv/bin/activate
west build -b nrf52840dk/nrf52840 samples/hello_world
```

**Rebuild from scratch**:
```bash
west build -p always -b nrf52840dk/nrf52840 samples/hello_world
```

**Build with custom overlay**:
```bash
west build -b nrf52840dk/nrf52840 samples/sensor/bme280 \
    --extra-dtc-overlay boards/custom_board.overlay
```

**Build and flash**:
```bash
west build -b nrf52840dk/nrf52840 samples/blinky
west flash
```

**Menu configuration**:
```bash
west build -t menuconfig
west build -t guiconfig  # GUI version
```

