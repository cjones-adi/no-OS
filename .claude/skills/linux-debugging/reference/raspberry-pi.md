# Raspberry Pi 4 Testing

## Serial Console Setup

**Hardware connection**:
- GPIO 14 (TXD) → USB-Serial RX
- GPIO 15 (RXD) → USB-Serial TX
- GND → GND

**/boot/cmdline.txt**:
```
console=serial0,115200 console=tty1 root=/dev/mmcblk0p2 rootwait
```

**/boot/config.txt**:
```
enable_uart=1
```

**Connect from host**:
```bash
screen /dev/ttyUSB0 115200
# or
minicom -D /dev/ttyUSB0 -b 115200
```

## Network Boot (TFTP + NFS)

Faster development iteration - build kernel on host, Pi boots from network.

**TFTP server on host**:
```bash
sudo apt install tftpd-hpa

# Copy kernel and DTB
sudo cp arch/arm64/boot/Image /srv/tftp/kernel8.img
sudo cp arch/arm64/boot/dts/broadcom/bcm2711-rpi-4-b.dtb /srv/tftp/
```

**NFS root on host**:
```bash
sudo apt install nfs-kernel-server

# /etc/exports
/nfs/rpi4 *(rw,sync,no_subtree_check,no_root_squash)

sudo exportfs -ra
```

**Pi boot configuration** (`/boot/cmdline.txt`):
```
console=serial0,115200 root=/dev/nfs nfsroot=192.168.1.100:/nfs/rpi4,vers=3,tcp ip=dhcp rootwait rw
```

## Devicetree Overlays

For adding hardware without recompiling the full DTB.

**Create overlay** (`ad7124-overlay.dts`):
```dts
/dts-v1/;
/plugin/;

/ {
	compatible = "brcm,bcm2711";

	fragment@0 {
		target = <&spi0>;
		__overlay__ {
			#address-cells = <1>;
			#size-cells = <0>;

			ad7124@0 {
				compatible = "adi,ad7124-4";
				reg = <0>;
				spi-max-frequency = <5000000>;
				interrupts = <25 IRQ_TYPE_EDGE_FALLING>;
				interrupt-parent = <&gpio>;
			};
		};
	};
};
```

**Compile and install**:
```bash
dtc -@ -I dts -O dtb -o ad7124.dtbo ad7124-overlay.dts
sudo cp ad7124.dtbo /boot/overlays/

# /boot/config.txt
dtoverlay=ad7124

sudo reboot
```

**Verify**:
```bash
# Check if device appeared
ls /sys/bus/iio/devices/

# View compiled devicetree
dtc -I fs -O dts /sys/firmware/devicetree/base | less
```

## Raspberry Pi Debugging Tips

**Early printk for boot issues**:
```bash
# /boot/cmdline.txt
earlyprintk console=serial0,115200
```

**Kernel crash debugging**:
```bash
# Enable more verbose oops
echo 1 > /proc/sys/kernel/panic_on_oops

# Or keep running after oops
echo 0 > /proc/sys/kernel/panic_on_oops
```

## Building for Raspberry Pi

### Cross-Compilation

```bash
# Install toolchain
sudo apt install gcc-aarch64-linux-gnu

# Configure
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- bcm2711_defconfig

# Build
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc) Image modules dtbs

# Install modules
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- INSTALL_MOD_PATH=/nfs/rpi4 modules_install
```

### Copying to Pi

```bash
# Copy kernel
sudo cp arch/arm64/boot/Image /boot/kernel8.img

# Copy device trees
sudo cp arch/arm64/boot/dts/broadcom/*.dtb /boot/

# Install modules
sudo make modules_install

sudo reboot
```

## Testing Hardware Interfaces

### SPI Testing

```bash
# Check SPI device appears
ls /dev/spidev*

# Enable SPI in config.txt
dtparam=spi=on

# Test with spidev
echo "Hello" > /dev/spidev0.0
```

### I2C Testing

```bash
# Install tools
sudo apt install i2c-tools

# Scan bus
i2cdetect -y 1

# Read register
i2cget -y 1 0x48 0x00

# Write register
i2cset -y 1 0x48 0x01 0xFF
```

### GPIO Testing

```bash
# Export GPIO
echo 17 > /sys/class/gpio/export

# Set direction
echo out > /sys/class/gpio/gpio17/direction

# Set value
echo 1 > /sys/class/gpio/gpio17/value

# Read value
cat /sys/class/gpio/gpio17/value
```

## Common Raspberry Pi Issues

### Device Not Probing

**Check devicetree**:
```bash
# View loaded device tree
dtc -I fs -O dts /sys/firmware/devicetree/base | grep -A 20 spi

# Verify overlay loaded
vcgencmd get_config int | grep dtoverlay
```

### SPI Issues

**Check SPI enabled**:
```bash
# /boot/config.txt
dtparam=spi=on

# Verify driver loaded
lsmod | grep spi
```

### Performance Issues

**CPU frequency scaling**:
```bash
# Disable frequency scaling for testing
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

**Check throttling**:
```bash
vcgencmd get_throttled
# 0x0 = no throttling
# 0x50000 = under-voltage occurred
```
