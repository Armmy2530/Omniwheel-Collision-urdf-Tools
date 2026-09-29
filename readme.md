# Omni Wheel URDF Generator & 3D Web Studio

This repository provides tools and an interactive Web GUI for designing, visualizing, and generating URDF/XACRO collision models for omni-directional wheels with multiple rollers.

## Features

- 🌐 **Interactive 3D Web Studio**: Real-time WebGL/Three.js 3D visualization of wheel hub, rollers (spheres & cylinder barrels), collision wireframes, and rotation axes.
- 🔵 **Multiple Collision Shapes**: Support for both **Sphere** (`<sphere>`) and **Cylinder** (`<cylinder>`) roller collision geometries with accurate inertia tensors and rotational alignment.
- ⚙️ **Parametric Layer Editor**: Configure multi-layer omni wheels with dynamic offsets, phase angles, and roller counts.
- 📐 **Multiple Orientation Methods**: Supports both `axis` (tangential rotation vector) and `rotation` (RPY pitch).
- 🤖 **URDF / Xacro Generation**: Instant Xacro collision macro snippet or complete standalone URDF model ready for ROS / RViz.
- 📦 **Pixi Package Management**: Reproducible environment and tasks managed with [pixi](https://pixi.sh).
- 💾 **Presets & YAML Management**: Built-in industry presets (100mm dual-layer, 125mm high-density, 150mm triple-layer heavy duty, etc.), plus upload/save YAML configs.

---

## Quick Start with Pixi

### 1. Launch the Web Studio GUI

Run the web visualizer application with:

```bash
pixi run start
# or
pixi run gui
```

Open your browser at **`http://localhost:8000`** to access the interactive 3D visualizer and generator.

### 2. Available Pixi Tasks

| Task | Command | Description |
|------|---------|-------------|
| **Start Web GUI** | `pixi run start` | Launches web visualizer on port 8000 with auto-reload |
| **Generate URDF** | `pixi run create-urdf` | Generates URDF collision model from YAML to `output.txt` |
| **Generate YAML** | `pixi run gen-yaml` | Generates wheel YAML config file |

---

## Architecture & File Structure

```
.
├── pixi.toml                         # Pixi package & task configuration
├── cli.py                            # Unified CLI tool
├── web/
│   ├── app.py                        # FastAPI web server & REST API
│   └── static/
│       ├── index.html                # Web GUI interface
│       ├── css/style.css             # Robotics CAD styling
│       └── js/app.js                 # Three.js 3D engine & reactive UI
├── core/
│   └── omni_generator.py             # Shared calculations & URDF logic
└── wheel_config/
    ├── example.yaml                  # Example configuration template
    └── omni_wheel_config.yml         # Active configuration file
```

---

## CLI Usage (Alternative to Web GUI)

You can also use the unified `cli.py` directly or through Pixi:

### 1. Generate URDF / Xacro Snippet

```bash
pixi run create-urdf
# or specify custom input & output:
pixi run python cli.py create-urdf wheel_config/example.yaml -o custom_output.urdf
```

To generate a full standalone robot URDF (viewable in RViz):
```bash
pixi run python cli.py create-urdf wheel_config/omni_wheel_config.yml --standalone -o standalone_wheel.urdf
```

### 2. Generate YAML Configuration

```bash
pixi run gen-yaml
# or with a preset:
pixi run python cli.py gen-yaml --preset standard_dual_layer -o wheel_config/standard.yml
```

### 3. Launch Web GUI via CLI

```bash
pixi run python cli.py gui --port 8080 --reload
```

---

## Output Format

The generated URDF configuration includes:
- Roller position and orientation data
- XACRO macros for roller definition
- Individual roller joint configurations

Example output structure:
```xml
<xacro:roller prefix="${prefix}" num="1">
    <origin xyz="0.055750 -0.012000 0.000000" rpy="0.000000 0.000000 0.000000" />
    <axis xyz="0.000000 0.000000 1.000000" />
</xacro:roller>
```

---

## Notes

- All measurements are in SI units (meters, radians) in code, with millimeters (mm) displayed in the Web GUI for convenience.
- The visualization tool shows the wheel facing along the Y-axis.