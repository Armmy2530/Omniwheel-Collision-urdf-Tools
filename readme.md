# Omni Wheel URDF Generator

This repository contains Python scripts for generating URDF (Unified Robot Description Format) files for omni wheels with collision configurations. The tools help in creating optimize and accurate collision models for omni wheels with multiple rollers.

## Overview

The toolkit consists of several Python scripts:
1. `create_collision_urdf.py` - Main script to generate URDF collision configurations
2. `gen_yaml_for_omni.py` - Helper script to generate wheel configuration YAML files
3. `visualize_yaml_wheel_config.py` - Tool to visualize the wheel configuration

## Prerequisites

- Python 3.x
- Required Python packages:
  ```bash
  pip install pyyaml numpy matplotlib
  ```

## Usage

### 1. Wheel Configuration

There are two ways to create a wheel configuration:

#### Option A: Manual YAML Creation
Create a YAML configuration file in the `wheel_config` directory. You can use `example.yaml` as a template:

```yaml
wheel_radius: 0.035      # Wheel base radius in meters
tangent_radius: 0.020    # Radius of collision spheres in meters
roller_count: 8          # Number of rollers
# Position configuration for each roller
position:
- [0.0, 0.004625, [0.0, 0.0, 1.0]]    # [angle, offset, rotation_axis]
- [90.0, 0.004625, [-1.0, 0.0, 0.0]]   # Format: [angle(degrees), offset(m), rotation_axis]
# ... add more roller positions as needed
```

#### Option B: Generate Using Python Script
Use `gen_yaml_for_omni.py` to automatically generate the wheel configuration:

```python
# at bottom of gen_yaml_for_omni.py, modify these parameters as needed:
offsets_with_angles = [
    [0.012, 0],  # [offset_translation, offset_angle_degrees]
    # Add more layers if needed
]

generate_omni_wheel_yaml(
    offsets_with_angles=offsets_with_angles,
    rollers_per_layer=12,              # Number of rollers per layer
    roller_weight=0.01,                # Weight of each roller in kg
    tangent_radius=0.004,              # Radius of roller collision sphere in meters
    wheel_radius=0.06175,              # Radius of wheel base in meters
    roller_method='rotation',          # 'rotation' or 'axis'
    output_path="wheel_config/my_wheel_config.yml"
)
```

Key parameters for both methods:
- `wheel_radius`: Base radius of the wheel (meters)
- `tangent_radius`: Radius of each roller collision sphere (meters)
- `roller_count`: Total number of rollers
- `position`: List of roller configurations [angle(degrees), offset(m), rotation_axis]

### 2. Generate URDF Configuration

Run `create_collision_urdf.py` to generate the URDF configuration:

```bash
python3 create_collision_urdf.py
```

The script will:
1. Read the wheel configuration from `wheel_config/omni_wheel_config.yml`
2. Generate URDF components in `output.txt` including:
   - Roller positions and orientations
   - URDF macro for roller definition
   - URDF blocks for each roller

### 3. Visualize Configuration (Optional)

To verify your wheel configuration visually:

```bash
python3 visualize_yaml_wheel_config.py
```

This will display a 3D visualization of the roller positions and orientations.

## File Structure
```
.
├── create_collision_urdf.py          # Main URDF generator
├── gen_yaml_for_omni.py             # YAML configuration generator
├── visualize_yaml_wheel_config.py    # Configuration visualizer
└── wheel_config/
    ├── example.yaml                 # Example configuration
    └── omni_wheel_config.yml        # Active configuration file
```

## Output Format

The generated URDF configuration includes:
- Roller position and orientation data
- XACRO macros for roller definition
- Individual roller joint configurations

Example output structure:
```xml
<xacro:roller prefix="${prefix}" num="1">
    <origin xyz="0.0577 0.012 0.0" rpy="0.0 0.0 0.0" />
    <axis xyz="1.0 0.0 0.0" />
</xacro:roller>
```

## Notes

- All measurements are in SI units (meters, radians)
- Angles in YAML files are in degrees but are converted to radians in the URDF
- The visualization tool shows the wheel facing the Y-axis