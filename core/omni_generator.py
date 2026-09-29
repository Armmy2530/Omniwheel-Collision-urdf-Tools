import math
import yaml
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

MAX_DECIMAL_POINT = 6

class InlineList(list):
    pass

def inline_list_representer(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

try:
    yaml.add_representer(InlineList, inline_list_representer)
except Exception:
    pass


COLLIDER_MODELS = {
    'o11': {
        'name': 'Model O (11 Spheres)',
        'type': 'o',
        'count': 11,
        'description': 'Optimized 11-sphere continuous collider with center sphere for smoothest ground contact and minimum drift.'
    },
    's6': {
        'name': 'Model S6 (6 Spheres)',
        'type': 's',
        'count': 6,
        'description': '6-sphere collider with bearing notch gap (3 per side). ICRA 2024 recommended balance between drift and performance.'
    },
    's4': {
        'name': 'Model S4 (4 Spheres)',
        'type': 's',
        'count': 4,
        'description': '4-sphere collider with bearing notch gap (2 per side).'
    },
    's8': {
        'name': 'Model S8 (8 Spheres)',
        'type': 's',
        'count': 8,
        'description': '8-sphere collider with bearing notch gap (4 per side).'
    },
    's10': {
        'name': 'Model S10 (10 Spheres)',
        'type': 's',
        'count': 10,
        'description': '10-sphere collider with bearing notch gap (5 per side).'
    },
    'c7': {
        'name': 'Model C7 (7 Cylinders)',
        'type': 'c',
        'count': 7,
        'description': '7-cylinder tapered barrel collider matching the roller convex curvature.'
    },
    'c4': {
        'name': 'Model C4 (4 Cylinders)',
        'type': 'c',
        'count': 4,
        'description': '4-cylinder collider with center gap for bearing notch (2 per side).'
    },
    'sphere': {
        'name': 'Single Sphere (1S)',
        'type': 'sphere',
        'count': 1,
        'description': 'Standard single sphere collision geometry.'
    },
    'cylinder': {
        'name': 'Single Cylinder (1C)',
        'type': 'cylinder',
        'count': 1,
        'description': 'Standard single cylinder collision geometry.'
    }
}


def get_collider_subelements(
    collider_type: str,
    wheel_radius: float,
    tangent_radius: float,
    roller_length: float
) -> List[Dict[str, Any]]:
    """
    Generate the geometric subelements for a roller collider according to
    'Simulation Modeling of Highly Dynamic Omnidirectional Mobile Robots Based on Real-World Data' (ICRA 2024).
    """
    R = float(wheel_radius)
    r0 = float(tangent_radius)
    L = float(roller_length)
    ctype = str(collider_type).lower().strip()

    def r_profile(u: float) -> float:
        """Ideal barrel radius of omni roller at axial offset u."""
        val = R**2 - u**2
        if val > 0:
            return max(0.25 * r0, math.sqrt(val) - (R - r0))
        return r0 * 0.5

    subelements = []

    if ctype in ('7c', 'c7'):
        n = 7
        h = L / n
        for i in range(n):
            u = -L / 2.0 + (i + 0.5) * h
            subelements.append({
                'type': 'cylinder',
                'u': round(u, 6),
                'radius': round(r_profile(u), 6),
                'length': round(h, 6)
            })

    elif ctype in ('4c', 'c4'):
        n_half = 2
        gap = 0.20 * L
        L_half = (L - gap) / 2.0
        h = L_half / n_half
        # Negative half
        for i in range(n_half):
            u = -(gap / 2.0 + (i + 0.5) * h)
            subelements.append({
                'type': 'cylinder',
                'u': round(u, 6),
                'radius': round(r_profile(u), 6),
                'length': round(h, 6)
            })
        # Positive half
        for i in range(n_half):
            u = gap / 2.0 + (i + 0.5) * h
            subelements.append({
                'type': 'cylinder',
                'u': round(u, 6),
                'radius': round(r_profile(u), 6),
                'length': round(h, 6)
            })

    elif ctype in ('s4', '4s', 's6', '6s', 's8', '8s', 's10', '10s'):
        n_spheres = int(''.join(filter(str.isdigit, ctype)))
        k = n_spheres // 2
        gap = 0.18 * L
        L_half = (L - gap) / 2.0
        for i in range(k):
            u_mag = gap / 2.0 + (i + 0.5) / k * L_half
            subelements.append({
                'type': 'sphere',
                'u': round(-u_mag, 6),
                'radius': round(r_profile(-u_mag), 6)
            })
            subelements.append({
                'type': 'sphere',
                'u': round(u_mag, 6),
                'radius': round(r_profile(u_mag), 6)
            })

    elif ctype in ('o', 'o11', '11s'):
        n_spheres = 11
        k = (n_spheres - 1) // 2  # 5 on each side
        # Center sphere
        subelements.append({
            'type': 'sphere',
            'u': 0.0,
            'radius': round(r_profile(0.0), 6)
        })
        for j in range(1, k + 1):
            u = (j / (k + 0.5)) * (L / 2.0)
            subelements.append({
                'type': 'sphere',
                'u': round(-u, 6),
                'radius': round(r_profile(-u), 6)
            })
            subelements.append({
                'type': 'sphere',
                'u': round(u, 6),
                'radius': round(r_profile(u), 6)
            })

    elif ctype == 'cylinder':
        subelements.append({
            'type': 'cylinder',
            'u': 0.0,
            'radius': round(r0, 6),
            'length': round(L, 6)
        })
    else:  # 'sphere' or fallback
        subelements.append({
            'type': 'sphere',
            'u': 0.0,
            'radius': round(r0, 6)
        })

    subelements.sort(key=lambda s: s['u'])
    return subelements


def compute_compound_inertia(subelements: List[Dict[str, Any]], total_mass: float) -> Tuple[float, float, float]:
    """Compute compound moments of inertia (ixx, iyy, izz) for roller with multiple subelements."""
    volumes = []
    for s in subelements:
        r = s['radius']
        if s['type'] == 'cylinder':
            h = s.get('length', 0.001)
            v = math.pi * r**2 * h
        else:
            v = (4.0 / 3.0) * math.pi * r**3
        volumes.append(max(v, 1e-9))

    v_total = sum(volumes)
    izz = 0.0  # spin axis (local Z)
    ixx = 0.0  # transverse
    iyy = 0.0  # transverse

    for s, v in zip(subelements, volumes):
        m_i = total_mass * (v / v_total)
        r = s['radius']
        u = s['u']
        if s['type'] == 'cylinder':
            h = s.get('length', 0.001)
            i_spin = 0.5 * m_i * r**2
            i_trans = (1.0 / 12.0) * m_i * (3 * r**2 + h**2) + m_i * u**2
        else:
            i_spin = 0.4 * m_i * r**2
            i_trans = 0.4 * m_i * r**2 + m_i * u**2

        izz += i_spin
        ixx += i_trans
        iyy += i_trans

    return round(ixx, 8), round(iyy, 8), round(izz, 8)


def calculate_roller_positions_from_layers(
    wheel_radius: float,
    tangent_radius: float,
    roller_weight: float,
    roller_method: str = "rotation",
    layers: List[Dict[str, Any]] = None,
    global_rollers_per_layer: int = 8,
    roller_shape: str = "o11",
    roller_length: Optional[float] = None
) -> Dict[str, Any]:
    """Generate complete omni wheel configuration from layer parameters."""
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
    collider_model = roller_shape if roller_shape in COLLIDER_MODELS else 'o11'

    config = {
        'wheel_radius': float(wheel_radius),
        'tangent_radius': float(tangent_radius),
        'roller_shape': collider_model,
        'collider_type': collider_model,
        'roller_length': actual_length,
        'roller_weight': float(roller_weight),
        'roller_count': len(positions),
        'roller_method': roller_method,
        'position': positions,
        'layer_info': layer_info
    }
    return config


def compute_roller_data(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compute 3D position, orientation, axis, and compound collider subelements for each roller."""
    roller_data = []
    wheel_radius = float(config.get('wheel_radius', 0.05))
    tangent_radius = float(config.get('tangent_radius', 0.01))
    roller_weight = float(config.get('roller_weight', 0.01))
    method = config.get('roller_method', 'rotation')
    amp = wheel_radius - tangent_radius
    layer_info = config.get('layer_info', [])
    collider_type = config.get('collider_type', config.get('roller_shape', 'o11'))
    roller_length = float(config.get('roller_length', round(tangent_radius * 2.5, 4)))

    subelements = get_collider_subelements(collider_type, wheel_radius, tangent_radius, roller_length)
    ixx, iyy, izz = compute_compound_inertia(subelements, roller_weight)

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
            'layer': layer_idx,
            'subelements': subelements,
            'inertia': {'ixx': ixx, 'iyy': iyy, 'izz': izz}
        })

    return roller_data


def generate_urdf_snippet(config: Dict[str, Any], roller_data: List[Dict[str, Any]], prefix: str = "${prefix}") -> str:
    """Generate xacro macro and roller instantiations with paper collider models (C, S, O)."""
    roller_weight = float(config.get('roller_weight', 0.01))
    tangent_radius = float(config.get('tangent_radius', 0.01))
    wheel_radius = float(config.get('wheel_radius', 0.05))
    collider_type = config.get('collider_type', config.get('roller_shape', 'o11'))
    roller_length = float(config.get('roller_length', round(tangent_radius * 2.5, 4)))
    method = config.get('roller_method', 'rotation')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sample_subs = get_collider_subelements(collider_type, wheel_radius, tangent_radius, roller_length)
    ixx, iyy, izz = compute_compound_inertia(sample_subs, roller_weight)
    model_info = COLLIDER_MODELS.get(collider_type, {'name': collider_type.upper(), 'description': ''})

    lines = [
        "<!-- =================================================================================== -->",
        f"<!-- Omni Wheel Collision URDF - Autogenerated at {now} -->",
        f"<!-- Collider Model: {model_info['name']} (from ICRA 2024 paper) -->",
        f"<!-- Wheel Radius: {wheel_radius}m, Roller Radius: {tangent_radius}m, Sub-colliders per roller: {len(sample_subs)} -->",
        "<!-- =================================================================================== -->\n",
        f'<xacro:property name="roller_mass" value="{roller_weight}" />',
        f'<xacro:property name="roller_radius" value="{tangent_radius}" />',
        f'<xacro:property name="roller_length" value="{roller_length}" />\n'
    ]

    if method == 'rotation':
        # In rotation method, link local Z is the spin axis for all rollers
        lines.append(f'<!-- Roller Macro Definition ({model_info["name"]} Compound Collision & Inertia) -->')
        lines.append('<xacro:macro name="roller" params="prefix num *joint_origin *joint_axis">')
        lines.append('    <link name="roller_${prefix}_${num}_link">')
        lines.append('        <inertial>')
        lines.append('            <origin xyz="0 0 0" rpy="0 0 0" />')
        lines.append('            <mass value="${roller_mass}" />')
        lines.append(f'            <inertia ixx="{ixx:.8f}" ixy="0" ixz="0" iyy="{iyy:.8f}" iyz="0" izz="{izz:.8f}" />')
        lines.append('        </inertial>')
        for idx, sub in enumerate(sample_subs):
            u = sub['u']
            r = sub['radius']
            if sub['type'] == 'cylinder':
                h = sub.get('length', 0.001)
                lines.append(f'        <!-- Sub-element {idx+1}: Cylinder at u={u*1000:.2f}mm -->')
                lines.append('        <collision>')
                lines.append(f'            <origin xyz="0 0 {u:.6f}" rpy="0 0 0" />')
                lines.append('            <geometry>')
                lines.append(f'                <cylinder radius="{r:.6f}" length="{h:.6f}" />')
                lines.append('            </geometry>')
                lines.append('        </collision>')
            else:
                lines.append(f'        <!-- Sub-element {idx+1}: Sphere at u={u*1000:.2f}mm -->')
                lines.append('        <collision>')
                lines.append(f'            <origin xyz="0 0 {u:.6f}" rpy="0 0 0" />')
                lines.append('            <geometry>')
                lines.append(f'                <sphere radius="{r:.6f}" />')
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
    else:
        # In axis method, each roller passes its collision elements
        lines.append(f'<!-- Roller Macro Definition ({model_info["name"]} Compound Collision & Inertia) -->')
        lines.append('<xacro:macro name="roller" params="prefix num *joint_origin *joint_axis *collisions">')
        lines.append('    <link name="roller_${prefix}_${num}_link">')
        lines.append('        <inertial>')
        lines.append('            <origin xyz="0 0 0" rpy="0 0 0" />')
        lines.append('            <mass value="${roller_mass}" />')
        lines.append(f'            <inertia ixx="{ixx:.8f}" ixy="0" ixz="0" iyy="{iyy:.8f}" iyz="0" izz="{izz:.8f}" />')
        lines.append('        </inertial>')
        lines.append('        <xacro:insert_block name="collisions" />')
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
            theta_rad = math.radians(item['theta_deg'])
            sin_t = math.sin(theta_rad)
            cos_t = math.cos(theta_rad)
            c_rpy_str = f"0.0 {-theta_rad:.6f} 0.0"

            lines.append(f'<xacro:roller prefix="{prefix}" num="{i}">')
            lines.append(f'    <origin xyz="{pos}" rpy="{rpy}" />')
            lines.append(f'    <axis xyz="{axis}" />')
            lines.append('    <collisions>')
            for sub in item.get('subelements', sample_subs):
                u = sub['u']
                r = sub['radius']
                sub_x = -u * sin_t
                sub_z = u * cos_t
                if sub['type'] == 'cylinder':
                    h = sub.get('length', 0.001)
                    lines.append('        <collision>')
                    lines.append(f'            <origin xyz="{sub_x:.6f} 0 {sub_z:.6f}" rpy="{c_rpy_str}" />')
                    lines.append('            <geometry>')
                    lines.append(f'                <cylinder radius="{r:.6f}" length="{h:.6f}" />')
                    lines.append('            </geometry>')
                    lines.append('        </collision>')
                else:
                    lines.append('        <collision>')
                    lines.append(f'            <origin xyz="{sub_x:.6f} 0 {sub_z:.6f}" rpy="0 0 0" />')
                    lines.append('            <geometry>')
                    lines.append(f'                <sphere radius="{r:.6f}" />')
                    lines.append('            </geometry>')
                    lines.append('        </collision>')
            lines.append('    </collisions>')
            lines.append('</xacro:roller>')

    return "\n".join(lines)


def generate_full_standalone_urdf(config: Dict[str, Any], roller_data: List[Dict[str, Any]], wheel_name: str = "omni_wheel") -> str:
    """Generate a complete standalone, valid XML URDF file viewable in ROS RViz / Gazebo."""
    wheel_radius = float(config.get('wheel_radius', 0.05))
    tangent_radius = float(config.get('tangent_radius', 0.01))
    roller_weight = float(config.get('roller_weight', 0.01))
    collider_type = config.get('collider_type', config.get('roller_shape', 'o11'))
    roller_length = float(config.get('roller_length', round(tangent_radius * 2.5, 4)))
    method = config.get('roller_method', 'rotation')
    hub_weight = 0.3

    sample_subs = get_collider_subelements(collider_type, wheel_radius, tangent_radius, roller_length)
    ixx, iyy, izz = compute_compound_inertia(sample_subs, roller_weight)

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
        theta_rad = math.radians(item['theta_deg'])
        sin_t = math.sin(theta_rad)
        cos_t = math.cos(theta_rad)
        c_rpy_str = f"0.0 {-theta_rad:.6f} 0.0"

        subs = item.get('subelements', sample_subs)

        lines.append(f'  <!-- Roller {i} -->')
        lines.append(f'  <link name="{wheel_name}_roller_{i}_link">')
        lines.append(f'    <inertial>')
        lines.append(f'      <origin xyz="0 0 0" rpy="0 0 0"/>')
        lines.append(f'      <mass value="{roller_weight}"/>')
        lines.append(f'      <inertia ixx="{ixx:.8f}" ixy="0" ixz="0" iyy="{iyy:.8f}" iyz="0" izz="{izz:.8f}"/>')
        lines.append(f'    </inertial>')

        # Collision sub-elements
        for sub in subs:
            u = sub['u']
            r = sub['radius']
            if method == 'rotation':
                sub_xyz = f"0 0 {u:.6f}"
                sub_rpy = "0 0 0"
            else:
                sub_x = -u * sin_t
                sub_z = u * cos_t
                sub_xyz = f"{sub_x:.6f} 0 {sub_z:.6f}"
                sub_rpy = c_rpy_str if sub['type'] == 'cylinder' else "0 0 0"

            if sub['type'] == 'cylinder':
                h = sub.get('length', 0.001)
                lines.append(f'    <collision>')
                lines.append(f'      <origin xyz="{sub_xyz}" rpy="{sub_rpy}"/>')
                lines.append(f'      <geometry><cylinder radius="{r:.6f}" length="{h:.6f}"/></geometry>')
                lines.append(f'    </collision>')
            else:
                lines.append(f'    <collision>')
                lines.append(f'      <origin xyz="{sub_xyz}" rpy="{sub_rpy}"/>')
                lines.append(f'      <geometry><sphere radius="{r:.6f}"/></geometry>')
                lines.append(f'    </collision>')

        # Visual representation (primary envelope)
        if method == 'rotation':
            vis_rpy = "0 0 0"
        else:
            vis_rpy = c_rpy_str
        lines.append(f'    <visual>')
        lines.append(f'      <origin xyz="0 0 0" rpy="{vis_rpy}"/>')
        lines.append(f'      <geometry><cylinder radius="{tangent_radius}" length="{roller_length}"/></geometry>')
        lines.append(f'      <material name="roller_mat_{i}"><color rgba="0.85 0.45 0.1 0.95"/></material>')
        lines.append(f'    </visual>')

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
    collider_type = config.get('collider_type', config.get('roller_shape', 'o11'))
    clean_config = {
        'wheel_radius': config.get('wheel_radius'),
        'tangent_radius': config.get('tangent_radius'),
        'roller_shape': collider_type,
        'collider_type': collider_type,
        'roller_length': config.get('roller_length', round(config.get('tangent_radius', 0.01) * 2.5, 4)),
        'roller_weight': config.get('roller_weight'),
        'roller_count': config.get('roller_count'),
        'roller_method': config.get('roller_method', 'rotation'),
        'position': [
            InlineList([pos[0], pos[1], InlineList(pos[2])]) for pos in config.get('position', [])
        ]
    }
    return yaml.dump(clean_config, sort_keys=False)


PRESETS = {
    "paper_model_o": {
        "name": "Paper Model O (11-Sphere Optimized, 100mm)",
        "description": "ICRA 2024 Model O with 11 overlapping spheres and central sphere for smoothest contact and minimum drift.",
        "wheel_radius": 0.050,
        "tangent_radius": 0.008,
        "collider_type": "o11",
        "roller_shape": "o11",
        "roller_length": 0.018,
        "roller_weight": 0.012,
        "roller_method": "rotation",
        "global_rollers_per_layer": 8,
        "layers": [
            {"offset": -0.009, "angle": 0.0, "rollers": 8},
            {"offset": 0.009, "angle": 22.5, "rollers": 8}
        ]
    },
    "paper_model_s6": {
        "name": "Paper Model S6 (6-Sphere Notch, 100mm)",
        "description": "ICRA 2024 Model S6 (3 spheres/side, bearing notch gap). Best balance between drift and simulation real-time factor.",
        "wheel_radius": 0.050,
        "tangent_radius": 0.008,
        "collider_type": "s6",
        "roller_shape": "s6",
        "roller_length": 0.018,
        "roller_weight": 0.012,
        "roller_method": "rotation",
        "global_rollers_per_layer": 8,
        "layers": [
            {"offset": -0.009, "angle": 0.0, "rollers": 8},
            {"offset": 0.009, "angle": 22.5, "rollers": 8}
        ]
    },
    "paper_model_c7": {
        "name": "Paper Model C7 (7-Cylinder Barrel, 100mm)",
        "description": "ICRA 2024 Model C7 with 7 concentric cylinders matching roller curvature.",
        "wheel_radius": 0.050,
        "tangent_radius": 0.008,
        "collider_type": "c7",
        "roller_shape": "c7",
        "roller_length": 0.018,
        "roller_weight": 0.012,
        "roller_method": "rotation",
        "global_rollers_per_layer": 8,
        "layers": [
            {"offset": -0.009, "angle": 0.0, "rollers": 8},
            {"offset": 0.009, "angle": 22.5, "rollers": 8}
        ]
    },
    "paper_model_c4": {
        "name": "Paper Model C4 (4-Cylinder Notch, 100mm)",
        "description": "ICRA 2024 Model C4 with 4 cylinders and center gap for roller bearing notch.",
        "wheel_radius": 0.050,
        "tangent_radius": 0.008,
        "collider_type": "c4",
        "roller_shape": "c4",
        "roller_length": 0.018,
        "roller_weight": 0.012,
        "roller_method": "rotation",
        "global_rollers_per_layer": 8,
        "layers": [
            {"offset": -0.009, "angle": 0.0, "rollers": 8},
            {"offset": 0.009, "angle": 22.5, "rollers": 8}
        ]
    },
    "standard_dual_layer": {
        "name": "Standard Dual-Layer (100mm, 2x8 rollers)",
        "description": "Standard 100mm omni wheel with 2 offset layers of 8 rollers each (total 16).",
        "wheel_radius": 0.050,
        "tangent_radius": 0.008,
        "collider_type": "o11",
        "roller_shape": "o11",
        "roller_length": 0.016,
        "roller_weight": 0.012,
        "roller_method": "rotation",
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
        "collider_type": "s6",
        "roller_shape": "s6",
        "roller_length": 0.015,
        "roller_weight": 0.010,
        "roller_method": "rotation",
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
        "collider_type": "o11",
        "roller_shape": "o11",
        "roller_length": 0.020,
        "roller_weight": 0.025,
        "roller_method": "rotation",
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
        "collider_type": "sphere",
        "roller_shape": "sphere",
        "roller_length": 0.025,
        "roller_weight": 0.015,
        "roller_method": "rotation",
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
        "collider_type": "c7",
        "roller_shape": "c7",
        "roller_length": 0.0175,
        "roller_weight": 0.008,
        "roller_method": "rotation",
        "global_rollers_per_layer": 10,
        "layers": [
            {"offset": 0.0, "angle": 0.0, "rollers": 10}
        ]
    }
}
