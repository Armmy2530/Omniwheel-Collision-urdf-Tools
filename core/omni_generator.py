import math
import yaml
from datetime import datetime
from typing import List, Dict, Any, Optional

MAX_DECIMAL_POINT = 6

class InlineList(list):
    pass

def inline_list_representer(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

try:
    yaml.add_representer(InlineList, inline_list_representer)
except Exception:
    pass


def calculate_roller_positions_from_layers(
    wheel_radius: float,
    tangent_radius: float,
    roller_weight: float,
    roller_method: str,
    layers: List[Dict[str, Any]],
    global_rollers_per_layer: int = 8,
    roller_shape: str = "sphere",
    roller_length: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate complete omni wheel configuration from layer parameters.
    layers: list of dicts: {'offset': float (m), 'angle': float (deg), 'rollers': int (optional)}
    roller_shape: 'sphere' or 'cylinder'
    roller_length: cylinder length in meters (default: tangent_radius * 2.5)
    """
    positions = []
    layer_info = []

    for l_idx, layer in enumerate(layers):
        offset = float(layer.get('offset', 0.0))
        offset_angle = float(layer.get('angle', 0.0))
        num_rollers = int(layer.get('rollers', global_rollers_per_layer))

        for i in range(num_rollers):
            base_theta = 360.0 * i / num_rollers
            theta = (base_theta + offset_angle) % 360.0
            angle_rad = math.radians(theta + 90.0)

            # Rotation axis tangent to circumference in X-Z plane: [-sin(theta), 0, cos(theta)]
            rot_axis = [math.cos(angle_rad), 0.0, math.sin(angle_rad)]

            positions.append([
                round(theta, 4),
                round(offset, 6),
                [round(c, 6) for c in rot_axis]
            ])
            layer_info.append(l_idx)

    actual_length = float(roller_length) if roller_length is not None else round(float(tangent_radius) * 2.5, 4)

    config = {
        'wheel_radius': float(wheel_radius),
        'tangent_radius': float(tangent_radius),
        'roller_shape': roller_shape if roller_shape in ('sphere', 'cylinder') else 'sphere',
        'roller_length': actual_length,
        'roller_weight': float(roller_weight),
        'roller_count': len(positions),
        'roller_method': roller_method,
        'position': positions,
        'layer_info': layer_info
    }
    return config


def compute_roller_data(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compute 3D position, orientation, and axis for each roller.
    Returns list of dicts with formatted coordinates and numbers.
    """
    roller_data = []
    wheel_radius = float(config.get('wheel_radius', 0.05))
    tangent_radius = float(config.get('tangent_radius', 0.01))
    method = config.get('roller_method', 'axis')
    amp = wheel_radius - tangent_radius
    layer_info = config.get('layer_info', [])

    for i, item in enumerate(config.get('position', [])):
        theta = float(item[0])
        offset = float(item[1])
        axis = [float(x) for x in item[2]]

        rad_theta = math.radians(theta)
        x = round(amp * math.cos(rad_theta), MAX_DECIMAL_POINT)
        y = round(offset, MAX_DECIMAL_POINT)
        z = round(amp * math.sin(rad_theta), MAX_DECIMAL_POINT)

        # World-space physical spin direction: tangent to the wheel circle in X-Z plane
        world_axis = [
            round(-math.sin(rad_theta), MAX_DECIMAL_POINT),
            0.0,
            round(math.cos(rad_theta), MAX_DECIMAL_POINT)
        ]

        if method == 'rotation':
            rpy = [0.0, round(math.radians(-theta), MAX_DECIMAL_POINT), 0.0]
            eff_axis = [0.0, 0.0, 1.0]
            cylinder_rpy = [0.0, 0.0, 0.0]
        else:
            rpy = [0.0, 0.0, 0.0]
            eff_axis = axis if (axis and any(axis)) else world_axis
            cylinder_rpy = [0.0, round(math.radians(-theta), MAX_DECIMAL_POINT), 0.0]

        layer_idx = layer_info[i] if i < len(layer_info) else 0

        roller_data.append({
            'id': i + 1,
            'theta_deg': theta,
            'offset_m': offset,
            'position': [x, y, z],
            'rpy': rpy,
            'cylinder_rpy': cylinder_rpy,
            'axis': eff_axis,
            'world_axis': world_axis,
            'layer': layer_idx
        })

    return roller_data


def generate_urdf_snippet(config: Dict[str, Any], roller_data: List[Dict[str, Any]], prefix: str = "${prefix}") -> str:
    """Generate xacro macro and roller instantiations with sphere or cylinder collision."""
    roller_weight = config.get('roller_weight', 0.01)
    tangent_radius = config.get('tangent_radius', 0.01)
    roller_shape = config.get('roller_shape', 'sphere')
    roller_length = config.get('roller_length', round(tangent_radius * 2.5, 4))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "<!-- =================================================================================== -->",
        f"<!-- Omni Wheel Collision URDF - Autogenerated at {now} -->",
        f"<!-- Wheel Radius: {config.get('wheel_radius')}m, Roller Radius: {tangent_radius}m, Shape: {roller_shape}, Rollers: {len(roller_data)} -->",
        "<!-- =================================================================================== -->\n",
        f'<xacro:property name="roller_mass" value="{roller_weight}" />',
        f'<xacro:property name="roller_radius" value="{tangent_radius}" />'
    ]

    if roller_shape == 'cylinder':
        lines.append(f'<xacro:property name="roller_length" value="{roller_length}" />\n')
        lines.append('<!-- Roller Macro Definition (Cylinder Collision & Inertia) -->')
        lines.append('<xacro:macro name="roller" params="prefix num *joint_origin *joint_axis *collision_origin">')
        lines.append('    <link name="roller_${prefix}_${num}_link">')
        lines.append('        <inertial>')
        lines.append('            <xacro:insert_block name="collision_origin" />')
        lines.append('            <mass value="${roller_mass}" />')
        lines.append(f'            <inertia ixx="{round((1/12)*roller_weight*(3*tangent_radius**2 + roller_length**2), 8)}" ixy="0" ixz="0"')
        lines.append(f'                     iyy="{round((1/12)*roller_weight*(3*tangent_radius**2 + roller_length**2), 8)}" iyz="0"')
        lines.append(f'                     izz="{round((1/2)*roller_weight*tangent_radius**2, 8)}" />')
        lines.append('        </inertial>')
        lines.append('        <collision>')
        lines.append('            <xacro:insert_block name="collision_origin" />')
        lines.append('            <geometry>')
        lines.append('                <cylinder radius="${roller_radius}" length="${roller_length}" />')
        lines.append('            </geometry>')
        lines.append('        </collision>')
        lines.append('    </link>')
        lines.append('    <joint name="roller_${prefix}_${num}_joint" type="continuous">')
        lines.append('        <xacro:insert_block name="joint_origin" />')
        lines.append('        <parent link="${prefix}_wheel_link" />')
        lines.append('        <child link="roller_${prefix}_${num}_link" />')
        lines.append('        <xacro:insert_block name="joint_axis" />')
        lines.append('    </joint>')
        lines.append('</xacro:macro>\n')
        lines.append('<!-- Individual Roller Joint and Link Instantiations -->')

        for item in roller_data:
            i = item['id']
            pos = " ".join(f"{v:.6f}" for v in item['position'])
            rpy = " ".join(f"{v:.6f}" for v in item['rpy'])
            axis = " ".join(f"{v:.6f}" for v in item['axis'])
            c_rpy = " ".join(f"{v:.6f}" for v in item.get('cylinder_rpy', [0.0, 0.0, 0.0]))
            lines.append(f'<xacro:roller prefix="{prefix}" num="{i}">')
            lines.append(f'    <origin xyz="{pos}" rpy="{rpy}" />')
            lines.append(f'    <axis xyz="{axis}" />')
            lines.append(f'    <origin xyz="0 0 0" rpy="{c_rpy}" />')
            lines.append('</xacro:roller>')
    else:
        # Sphere collision
        lines.append('\n<!-- Roller Macro Definition (Sphere Collision) -->')
        lines.append('<xacro:macro name="roller" params="prefix num *joint_origin *joint_axis">')
        lines.append('    <link name="roller_${prefix}_${num}_link">')
        lines.append('        <xacro:inertial_sphere mass="${roller_mass}" radius="${roller_radius}">')
        lines.append('            <origin xyz="0 0 0" rpy="0 0 0" />')
        lines.append('        </xacro:inertial_sphere>')
        lines.append('        <collision>')
        lines.append('            <origin xyz="0 0 0" rpy="0 0 0" />')
        lines.append('            <geometry>')
        lines.append('                <sphere radius="${roller_radius}" />')
        lines.append('            </geometry>')
        lines.append('        </collision>')
        lines.append('    </link>')
        lines.append('    <joint name="roller_${prefix}_${num}_joint" type="continuous">')
        lines.append('        <xacro:insert_block name="joint_origin" />')
        lines.append('        <parent link="${prefix}_wheel_link" />')
        lines.append('        <child link="roller_${prefix}_${num}_link" />')
        lines.append('        <xacro:insert_block name="joint_axis" />')
        lines.append('    </joint>')
        lines.append('</xacro:macro>\n')
        lines.append('<!-- Individual Roller Joint and Link Instantiations -->')

        for item in roller_data:
            i = item['id']
            pos = " ".join(f"{v:.6f}" for v in item['position'])
            rpy = " ".join(f"{v:.6f}" for v in item['rpy'])
            axis = " ".join(f"{v:.6f}" for v in item['axis'])
            lines.append(f'<xacro:roller prefix="{prefix}" num="{i}">')
            lines.append(f'    <origin xyz="{pos}" rpy="{rpy}" />')
            lines.append(f'    <axis xyz="{axis}" />')
            lines.append('</xacro:roller>')

    return "\n".join(lines)


def generate_full_standalone_urdf(config: Dict[str, Any], roller_data: List[Dict[str, Any]], wheel_name: str = "omni_wheel") -> str:
    """Generate a complete standalone, valid XML URDF file viewable in ROS RViz / Gazebo."""
    wheel_radius = config.get('wheel_radius', 0.05)
    tangent_radius = config.get('tangent_radius', 0.01)
    roller_weight = config.get('roller_weight', 0.01)
    roller_shape = config.get('roller_shape', 'sphere')
    roller_length = config.get('roller_length', round(tangent_radius * 2.5, 4))
    hub_width = 0.04
    hub_weight = 0.3

    lines = [
        '<?xml version="1.0"?>',
        f'<robot name="{wheel_name}_model">',
        f'  <!-- Base Footprint / Chassis Mount -->',
        f'  <link name="base_link">',
        f'    <visual>',
        f'      <origin xyz="0 0 0" rpy="0 0 0"/>',
        f'      <geometry>',
        f'        <sphere radius="0.005"/>',
        f'      </geometry>',
        f'      <material name="dark_gray"><color rgba="0.2 0.2 0.2 1.0"/></material>',
        f'    </visual>',
        f'  </link>\n',
        f'  <!-- Wheel Hub Link -->',
        f'  <link name="{wheel_name}_hub_link">',
        f'    <visual>',
        f'      <origin xyz="0 0 0" rpy="1.57079632679 0 0"/>',
        f'      <geometry>',
        f'        <cylinder radius="{round(wheel_radius - tangent_radius, 4)}" length="{round(tangent_radius * 2, 4)}"/>',
        f'      </geometry>',
        f'      <material name="hub_material"><color rgba="0.15 0.35 0.8 0.85"/></material>',
        f'    </visual>',
        f'    <collision>',
        f'      <origin xyz="0 0 0" rpy="1.57079632679 0 0"/>',
        f'      <geometry>',
        f'        <cylinder radius="{round(wheel_radius - tangent_radius * 1.5, 4)}" length="{round(tangent_radius * 1.8, 4)}"/>',
        f'      </geometry>',
        f'    </collision>',
        f'    <inertial>',
        f'      <mass value="{hub_weight}"/>',
        f'      <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001"/>',
        f'    </inertial>',
        f'  </link>\n',
        f'  <!-- Wheel Joint -->',
        f'  <joint name="{wheel_name}_joint" type="continuous">',
        f'    <parent link="base_link"/>',
        f'    <child link="{wheel_name}_hub_link"/>',
        f'    <origin xyz="0 0 {round(wheel_radius, 4)}" rpy="0 0 0"/>',
        f'    <axis xyz="0 1 0"/>',
        f'  </joint>\n'
    ]

    for item in roller_data:
        i = item['id']
        pos = " ".join(f"{v:.6f}" for v in item['position'])
        rpy = " ".join(f"{v:.6f}" for v in item['rpy'])
        axis = " ".join(f"{v:.6f}" for v in item['axis'])

        if roller_shape == 'cylinder':
            geom = f'<cylinder radius="{tangent_radius}" length="{roller_length}"/>'
            c_rpy = " ".join(f"{v:.6f}" for v in item.get('cylinder_rpy', [0.0, 0.0, 0.0]))
            ixx_val = round((1/12)*roller_weight*(3*tangent_radius**2 + roller_length**2), 8)
            izz_val = round((1/2)*roller_weight*tangent_radius**2, 8)
            origin_tag = f'<origin xyz="0 0 0" rpy="{c_rpy}"/>'
            inertia_tag = f'<inertia ixx="{ixx_val}" ixy="0" ixz="0" iyy="{ixx_val}" iyz="0" izz="{izz_val}"/>'
        else:
            geom = f'<sphere radius="{tangent_radius}"/>'
            origin_tag = '<origin xyz="0 0 0" rpy="0 0 0"/>'
            sph_i = round(0.4 * roller_weight * tangent_radius**2, 8)
            inertia_tag = f'<inertia ixx="{sph_i}" ixy="0" ixz="0" iyy="{sph_i}" iyz="0" izz="{sph_i}"/>'

        lines.append(f'  <!-- Roller {i} -->')
        lines.append(f'  <link name="{wheel_name}_roller_{i}_link">')
        lines.append(f'    <visual>')
        lines.append(f'      {origin_tag}')
        lines.append(f'      <geometry>{geom}</geometry>')
        lines.append(f'      <material name="roller_mat_{i}"><color rgba="0.85 0.45 0.1 0.95"/></material>')
        lines.append(f'    </visual>')
        lines.append(f'    <collision>')
        lines.append(f'      {origin_tag}')
        lines.append(f'      <geometry>{geom}</geometry>')
        lines.append(f'    </collision>')
        lines.append(f'    <inertial>')
        lines.append(f'      {origin_tag}')
        lines.append(f'      <mass value="{roller_weight}"/>')
        lines.append(f'      {inertia_tag}')
        lines.append(f'    </inertial>')
        lines.append(f'  </link>')
        lines.append(f'  <joint name="{wheel_name}_roller_{i}_joint" type="continuous">')
        lines.append(f'    <parent link="{wheel_name}_hub_link"/>')
        lines.append(f'    <child link="{wheel_name}_roller_{i}_link"/>')
        lines.append(f'    <origin xyz="{pos}" rpy="{rpy}"/>')
        lines.append(f'    <axis xyz="{axis}"/>')
        lines.append(f'  </joint>\n')

    lines.append('</robot>')
    return "\n".join(lines)


def generate_yaml_string(config: Dict[str, Any]) -> str:
    """Format config dictionary as clean readable YAML."""
    clean_config = {
        'wheel_radius': config.get('wheel_radius'),
        'tangent_radius': config.get('tangent_radius'),
        'roller_shape': config.get('roller_shape', 'sphere'),
    }
    if config.get('roller_shape') == 'cylinder':
        clean_config['roller_length'] = config.get('roller_length', round(config.get('tangent_radius', 0.01) * 2.5, 4))

    clean_config.update({
        'roller_weight': config.get('roller_weight'),
        'roller_count': config.get('roller_count'),
        'roller_method': config.get('roller_method', 'axis'),
        'position': [
            InlineList([pos[0], pos[1], InlineList(pos[2])]) for pos in config.get('position', [])
        ]
    })
    return yaml.dump(clean_config, sort_keys=False)


PRESETS = {
    "standard_dual_layer": {
        "name": "Standard Dual-Layer (100mm, 2x8 rollers)",
        "description": "Standard 100mm omni wheel with 2 offset layers of 8 rollers each (total 16).",
        "wheel_radius": 0.050,
        "tangent_radius": 0.008,
        "roller_weight": 0.012,
        "roller_method": "axis",
        "global_rollers_per_layer": 8,
        "layers": [
            {"offset": -0.009, "angle": 0.0, "rollers": 8},
            {"offset": 0.009, "angle": 22.5, "rollers": 8}
        ]
    },
    "dual_layer_12_rollers": {
        "name": "High-Density Dual-Layer (125mm, 2x12 rollers)",
        "description": "Smooth rolling dual-layer omni with 12 rollers per layer (24 total).",
        "wheel_radius": 0.06175,
        "tangent_radius": 0.006,
        "roller_weight": 0.010,
        "roller_method": "axis",
        "global_rollers_per_layer": 12,
        "layers": [
            {"offset": -0.012, "angle": 0.0, "rollers": 12},
            {"offset": 0.012, "angle": 15.0, "rollers": 12}
        ]
    },
    "triple_layer_heavy": {
        "name": "Triple-Layer Heavy Duty (150mm, 3x6 rollers)",
        "description": "3 staggered layers for maximum ground contact and load distribution.",
        "wheel_radius": 0.075,
        "tangent_radius": 0.010,
        "roller_weight": 0.025,
        "roller_method": "axis",
        "global_rollers_per_layer": 6,
        "layers": [
            {"offset": -0.016, "angle": 0.0, "rollers": 6},
            {"offset": 0.000, "angle": 20.0, "rollers": 6},
            {"offset": 0.016, "angle": 40.0, "rollers": 6}
        ]
    },
    "example_repo": {
        "name": "Repository Example (70mm, 2x4 rollers)",
        "description": "Configuration matching example.yaml in repo (8 rollers across 2 layers).",
        "wheel_radius": 0.035,
        "tangent_radius": 0.020,
        "roller_weight": 0.015,
        "roller_method": "axis",
        "global_rollers_per_layer": 4,
        "layers": [
            {"offset": 0.004625, "angle": 0.0, "rollers": 4},
            {"offset": 0.013875, "angle": 45.0, "rollers": 4}
        ]
    },
    "single_layer": {
        "name": "Single Layer (80mm, 10 rollers)",
        "description": "Single-layer omni wheel with 10 rollers centered at Y=0.",
        "wheel_radius": 0.040,
        "tangent_radius": 0.007,
        "roller_weight": 0.008,
        "roller_method": "axis",
        "global_rollers_per_layer": 10,
        "layers": [
            {"offset": 0.0, "angle": 0.0, "rollers": 10}
        ]
    }
}
