# Devicetree Validation

Complete guide to validating devicetree bindings and compiled devicetrees.

## dt_binding_check

Validates YAML schema files for correct syntax and structure.

### Basic Usage

```bash
# Validate specific binding
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad7944.yaml

# Validate all IIO bindings
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/

# Validate all bindings (takes a long time)
make dt_binding_check
```

### Common Errors and Solutions

#### Error: Incorrect YAML List Syntax

```
Error: properties:compatible:enum:0: 'adi,ad7944' is not of type 'object', 'boolean'
```

**Problem:**
```yaml
compatible:
  enum:
    adi,ad7944  # WRONG: Missing list indicator
```

**Solution:**
```yaml
compatible:
  enum:
    - adi,ad7944  # Correct: Note the '- ' prefix
    - adi,ad7985
```

#### Error: unevaluatedProperties with $ref

```
Error: 'unevaluatedProperties' is a dependency of '$ref'
```

**Problem:**
```yaml
$ref: /schemas/spi/spi-peripheral-props.yaml#

additionalProperties: false  # WRONG: Blocks properties from $ref
```

**Solution:**
```yaml
$ref: /schemas/spi/spi-peripheral-props.yaml#

unevaluatedProperties: false  # Correct: Use with $ref
```

#### Error: Invalid Schema Path

```
Error: '/schemas/types.yaml#/definitions/uint32' does not match '^/schemas/'
```

**Problem:**
```yaml
properties:
  adi,value:
    $ref: /schemas/types.yaml#/definitions/uint32  # Missing leading /
```

**Solution:**
```yaml
properties:
  adi,value:
    $ref: /schemas/types.yaml#/definitions/uint32  # Correct path
```

#### Error: Missing SPDX License

```
Error: File must start with SPDX license identifier
```

**Problem:**
```yaml
%YAML 1.2  # Missing SPDX!
---
```

**Solution:**
```yaml
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
```

#### Error: Invalid $id Format

```
Error: $id must start with 'http://devicetree.org/schemas/'
```

**Problem:**
```yaml
$id: http://example.com/schemas/iio/adc/adi,ad7944.yaml#
```

**Solution:**
```yaml
$id: http://devicetree.org/schemas/iio/adc/adi,ad7944.yaml#
```

#### Error: Missing Required Properties

```
Error: 'compatible' is a required property
```

**Solution:** Add to `required` list:
```yaml
required:
  - compatible
  - reg
  - avdd-supply
```

#### Error: Incorrect Pattern Syntax

```
Error: Pattern '^channel@[0-1]$' matches unexpected nodes
```

**Problem:**
```yaml
patternProperties:
  "channel@[0-1]":  # WRONG: Missing anchors
```

**Solution:**
```yaml
patternProperties:
  "^channel@[0-1]$":  # Correct: ^ and $ anchor the pattern
```

#### Error: Type Mismatch

```
Error: True is not of type 'object'
```

**Problem:**
```yaml
properties:
  vref-supply: true  # Too simple for complex property
```

**Solution:** Define properly or remove constraint:
```yaml
properties:
  vref-supply:
    description: External reference voltage regulator
```

## dtbs_check

Validates compiled devicetree files (.dtb) against bindings.

### Basic Usage

```bash
# Compile and validate all devicetrees for platform
make ARCH=arm zynq_xcomm_adv7511_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- dtbs_check

# Validate specific DTS file
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- zynqmp-zcu102-rev10-ad9081.dtb

# Check DTS against specific binding
make ARCH=arm64 DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad9081.yaml dtbs_check

# Check all Zynq devicetrees
make ARCH=arm dtbs_check 2>&1 | grep -A5 zynq
```

### Common Warnings and Fixes

#### Warning: Missing Required Property

```
Warning: /soc/spi@e0007000/adc@0: 'spi-max-frequency' is a required property
```

**Solution:** Add missing property to DTS:
```dts
&spi0 {
    adc@0 {
        compatible = "adi,ad7944";
        reg = <0>;
        spi-max-frequency = <50000000>;  // Add this
    };
};
```

#### Warning: Property Not in Schema

```
Warning: adc@0: 'avdd-supply' does not match any of the regexes
```

**Causes:**
1. Typo in DTS property name
2. Property not defined in binding schema

**Solution 1:** Fix typo in DTS:
```dts
adc@0 {
    avdd-supply = <&vdd>;  // Check spelling
};
```

**Solution 2:** Add property to binding:
```yaml
properties:
  avdd-supply:
    description: Analog supply voltage
```

#### Warning: Incorrect Property Value

```
Warning: adc@0:spi-max-frequency: 200000000 is greater than the maximum of 111111111
```

**Solution:** Fix value in DTS:
```dts
adc@0 {
    spi-max-frequency = <100000000>;  // Must be <= 111111111
};
```

#### Warning: Additional Properties Not Allowed

```
Warning: adc@0: 'unknown-prop' does not match any of the regexes: 'pinctrl-[0-9]+'
```

**Cause:** DTS has property not defined in binding, and binding uses `additionalProperties: false`

**Solution 1:** Remove unknown property from DTS
**Solution 2:** Add property to binding schema

#### Warning: Incorrect Node Name

```
Warning: 'adc' does not match '^.*@[0-9a-f]+$'
```

**Problem:**
```dts
spi {
    adc {  // WRONG: Missing address
        compatible = "adi,ad7944";
        reg = <0>;
    };
};
```

**Solution:**
```dts
spi {
    adc@0 {  // Correct: Node name matches reg address
        compatible = "adi,ad7944";
        reg = <0>;
    };
};
```

#### Warning: Phandle Not Found

```
Warning: adc@0: Failed to resolve 'vref-supply' phandle
```

**Problem:**
```dts
adc@0 {
    vref-supply = <&vref_ext>;  // vref_ext not defined
};
```

**Solution:** Define phandle target:
```dts
vref_ext: regulator@0 {
    compatible = "regulator-fixed";
    regulator-name = "vref-2.5V";
    regulator-min-microvolt = <2500000>;
    regulator-max-microvolt = <2500000>;
};

adc@0 {
    vref-supply = <&vref_ext>;  // Now defined
};
```

## Complete Validation Workflow

### Step-by-Step Validation

```bash
# 1. Create/modify YAML binding
vim Documentation/devicetree/bindings/iio/adc/adi,ad9083.yaml

# 2. Validate binding schema
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad9083.yaml

# 3. Fix any binding errors, repeat step 2 until clean

# 4. Create/modify DTS file
vim arch/arm64/boot/dts/xilinx/zynqmp-zcu102-rev10-ad9083.dts

# 5. Compile DTS to DTB
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- zynqmp-zcu102-rev10-ad9083.dtb

# 6. Check DTS against binding
make ARCH=arm64 DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad9083.yaml \
     zynqmp-zcu102-rev10-ad9083.dtb

# 7. Validate all DTS files for platform
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- dtbs_check

# 8. Fix warnings, repeat steps 4-7 until clean
```

### Local Testing Like CI

Run validation in Docker like Azure Pipelines does:

```bash
# Set environment for specific platform
export DEFCONFIG=zynq_xcomm_adv7511_defconfig
export ARCH=arm
export IMAGE=uImage
export CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT=1

# Run dockerized build with validation
./ci/travis/run-build-docker.sh

# Or run directly without Docker
export LOCAL_BUILD=y
export DO_NOT_DOCKERIZE=1
./ci/travis/run-build.sh
```

## Debugging Validation Issues

### Verbose Output

```bash
# Enable verbose dt_binding_check
make V=1 dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad7944.yaml

# Enable verbose dtbs_check
make V=1 ARCH=arm dtbs_check
```

### Check Compiled DTB

View compiled devicetree:

```bash
# Decompile DTB to DTS
dtc -I dtb -O dts -o output.dts arch/arm/boot/dts/xilinx/zynq-zc706-adv7511.dtb

# View decompiled DTS
less output.dts
```

### Check Schema Files

Validate JSON schema correctness:

```bash
# Install dt-schema tools
pip3 install dtschema

# Check schema file
dt-validate Documentation/devicetree/bindings/iio/adc/adi,ad7944.yaml
```

## Pre-Submission Checklist

Before submitting devicetree changes:

- [ ] Run `make dt_binding_check` on new/modified binding
- [ ] Run `make dtbs_check` on affected platform
- [ ] Verify DTS compiles without warnings
- [ ] Test on actual hardware (if available)
- [ ] Run checkpatch on DTS changes: `scripts/checkpatch.pl <patch>`
- [ ] Ensure binding follows naming conventions (vendor prefix, lowercase)
- [ ] Verify all required properties are documented
- [ ] Add example to binding showing realistic usage
- [ ] Update MAINTAINERS file if adding new subsystem

## CI/CD Integration

### Azure Pipelines Checks

ADI Linux kernel CI runs these validation steps:

1. Build kernel with `CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT=1`
2. Compile all devicetrees for platform
3. Run `dtbs_check` on compiled devicetrees
4. Check for warnings in build log

**Important:** CI tests multiple platforms:
- `zynq_xcomm_adv7511_defconfig` (ARM)
- `socfpga_adi_defconfig` (ARM)
- `adi_zynqmp_defconfig` (ARM64)
- `adi_versal_defconfig` (ARM64)

Ensure DTS changes work across all relevant platforms.

## Performance Tips

### Faster Validation

```bash
# Validate only changed binding
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad7944.yaml

# Skip clean build
make ARCH=arm dtbs_check  # Incremental build

# Parallel build
make -j$(nproc) ARCH=arm dtbs_check

# Validate single DTB
make ARCH=arm64 zynqmp-zcu102-rev10-ad9081.dtb
```

### Cache Schema Files

DT schema validation caches processed schemas:

```bash
# Cache location (automatically managed)
ls -la Documentation/devicetree/bindings/.cache/
```

Delete cache if seeing inconsistent validation:
```bash
rm -rf Documentation/devicetree/bindings/.cache/
make dt_binding_check
```
