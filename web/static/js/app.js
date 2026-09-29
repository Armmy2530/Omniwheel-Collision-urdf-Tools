/**
 * Omniwheel Collision URDF Studio - Interactive Frontend
 */

// Global State
const state = {
  wheel_radius_mm: 50.0,
  tangent_radius_mm: 8.0,
  roller_shape: 'o11',
  roller_length_mm: 18.0,
  roller_weight_kg: 0.012,
  roller_method: 'rotation',
  prefix: '${prefix}',
  wheel_name: 'omni_wheel',
  layers: [
    { offset_mm: -9.0, angle_deg: 0.0, rollers: 8 },
    { offset_mm: 9.0, angle_deg: 22.5, rollers: 8 }
  ],
  display: {
    showHub: true,
    showAxes: true,
    showGrid: true,
    showArrows: true,
    showWireframe: true,
    autoRotate: false
  },
  currentData: null,
  selectedRollerId: null
};

// Layer Color Palette
const LAYER_COLORS = [
  0x3b82f6, // Blue
  0xf97316, // Orange
  0x10b981, // Green
  0xa855f7, // Purple
  0xec4899, // Pink
  0xeab308  // Yellow
];

// Built-in Default Presets (Available instantly even offline)
const DEFAULT_PRESETS = {
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
    "roller_length": 0.020,
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
};

let presetsData = Object.assign({}, DEFAULT_PRESETS);

function populatePresetsDropdown(presets) {
  const select = document.getElementById('preset-selector');
  if (!select) return;
  select.innerHTML = '<option value="">-- Load Standard Preset --</option>';
  for (const [key, preset] of Object.entries(presets)) {
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = preset.name;
    select.appendChild(opt);
  }
}

function getColliderSubelementsJS(colliderType, wheelRadiusMm, tangentRadiusMm, rollerLengthMm) {
  const R = wheelRadiusMm;
  const r0 = tangentRadiusMm;
  const L = rollerLengthMm;
  const ctype = (colliderType || 'o11').toLowerCase().trim();

  function rProfile(u) {
    const val = R * R - u * u;
    if (val > 0) {
      return Math.max(0.25 * r0, Math.sqrt(val) - (R - r0));
    }
    return r0 * 0.5;
  }

  const subs = [];

  if (ctype === '7c' || ctype === 'c7') {
    const n = 7;
    const h = L / n;
    for (let i = 0; i < n; i++) {
      const u = -L / 2.0 + (i + 0.5) * h;
      subs.push({ type: 'cylinder', u_mm: u, radius_mm: rProfile(u), length_mm: h });
    }
  } else if (ctype === '4c' || ctype === 'c4') {
    const n_half = 2;
    const gap = 0.20 * L;
    const L_half = (L - gap) / 2.0;
    const h = L_half / n_half;
    for (let i = 0; i < n_half; i++) {
      const u = -(gap / 2.0 + (i + 0.5) * h);
      subs.push({ type: 'cylinder', u_mm: u, radius_mm: rProfile(u), length_mm: h });
    }
    for (let i = 0; i < n_half; i++) {
      const u = gap / 2.0 + (i + 0.5) * h;
      subs.push({ type: 'cylinder', u_mm: u, radius_mm: rProfile(u), length_mm: h });
    }
  } else if (/^s\d+$/i.test(ctype) || /^\d+s$/i.test(ctype)) {
    const nSpheres = parseInt(ctype.replace(/\D/g, '')) || 6;
    const k = Math.floor(nSpheres / 2);
    const gap = 0.18 * L;
    const L_half = (L - gap) / 2.0;
    for (let i = 0; i < k; i++) {
      const u_mag = gap / 2.0 + ((i + 0.5) / k) * L_half;
      subs.push({ type: 'sphere', u_mm: -u_mag, radius_mm: rProfile(-u_mag) });
      subs.push({ type: 'sphere', u_mm: u_mag, radius_mm: rProfile(u_mag) });
    }
  } else if (ctype === 'o' || ctype === 'o11' || ctype === '11s') {
    const nSpheres = 11;
    const k = Math.floor((nSpheres - 1) / 2);
    subs.push({ type: 'sphere', u_mm: 0.0, radius_mm: rProfile(0.0) });
    for (let j = 1; j <= k; j++) {
      const u = (j / (k + 0.5)) * (L / 2.0);
      subs.push({ type: 'sphere', u_mm: -u, radius_mm: rProfile(-u) });
      subs.push({ type: 'sphere', u_mm: u, radius_mm: rProfile(u) });
    }
  } else if (ctype === 'cylinder') {
    subs.push({ type: 'cylinder', u_mm: 0.0, radius_mm: r0, length_mm: L });
  } else {
    subs.push({ type: 'sphere', u_mm: 0.0, radius_mm: r0 });
  }

  subs.sort((a, b) => a.u_mm - b.u_mm);
  return subs;
}

function localComputeRollerData() {
  const amp = (state.wheel_radius_mm - state.tangent_radius_mm) / 1000.0;
  const roller_data = [];
  let id = 1;

  const sampleSubs = getColliderSubelementsJS(
    state.roller_shape,
    state.wheel_radius_mm,
    state.tangent_radius_mm,
    state.roller_length_mm
  ).map(s => ({
    type: s.type,
    u: s.u_mm / 1000.0,
    radius: s.radius_mm / 1000.0,
    length: (s.length_mm || 0) / 1000.0
  }));

  state.layers.forEach((layer, l_idx) => {
    const offset = layer.offset_mm / 1000.0;
    const num = parseInt(layer.rollers) || 8;
    for (let i = 0; i < num; i++) {
      const theta = (360.0 * i / num + layer.angle_deg) % 360.0;
      const rad = theta * Math.PI / 180.0;
      const x = amp * Math.cos(rad);
      const y = offset;
      const z = amp * Math.sin(rad);
      const world_axis = [-Math.sin(rad), 0.0, Math.cos(rad)];
      const rpy = state.roller_method === 'rotation' ? [0.0, -rad, 0.0] : [0.0, 0.0, 0.0];
      const axis = state.roller_method === 'rotation' ? [0.0, 0.0, 1.0] : world_axis;
      const cylinder_rpy = state.roller_method === 'axis' ? [0.0, -rad, 0.0] : [0.0, 0.0, 0.0];

      roller_data.push({
        id: id++,
        theta_deg: theta,
        offset_m: offset,
        position: [x, y, z],
        rpy: rpy,
        cylinder_rpy: cylinder_rpy,
        axis: axis,
        world_axis: world_axis,
        layer: l_idx,
        subelements: sampleSubs
      });
    }
  });

  return {
    roller_data: roller_data,
    metrics: {
      total_rollers: roller_data.length,
      outer_diameter_mm: state.wheel_radius_mm * 2,
      hub_diameter_mm: Math.max(0, (state.wheel_radius_mm - state.tangent_radius_mm) * 2),
      roller_diameter_mm: state.tangent_radius_mm * 2,
      total_roller_mass_kg: roller_data.length * state.roller_weight_kg
    }
  };
}

// Three.js Globals
let scene, camera, renderer, controls;
let orthoCamera, perspCamera;
let isOrthographic = true;
let frustumSize = 250;
let wheelGroup, hubMesh, gridHelper, axesHelper;
let rollerMeshes = [];
let arrowHelpers = [];
let raycaster, mouse;
let animationFrameId;

// Initialize function with safe fallbacks
function initializeApp() {
  populatePresetsDropdown(DEFAULT_PRESETS);

  try {
    initThreeJS();
    // Render immediate local 3D preview
    const initialData = localComputeRollerData();
    state.currentData = initialData;
    updateThreeScene(initialData);
    updateMetricsHUD(initialData.metrics);
  } catch (err) {
    console.error("Three.js init error:", err);
  }

  try {
    initEventListeners();
  } catch (err) {
    console.error("Event listeners error:", err);
  }

  renderLayersUI();
  loadPresetsList();
  loadSavedConfigsList();
  triggerCompute();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}

/* -------------------------------------------------------------
 * 1. Three.js Scene Initialization
 * ------------------------------------------------------------- */
function initThreeJS() {
  const container = document.getElementById('viewport-container');
  const width = (container && container.clientWidth) ? container.clientWidth : 800;
  const height = (container && container.clientHeight) ? container.clientHeight : 500;
  const aspect = width / height;

  // Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0f172a);

  // Orthographic Camera (Primary CAD-standard parallel projection)
  frustumSize = Math.max(160, state.wheel_radius_mm * 2.8);
  orthoCamera = new THREE.OrthographicCamera(
    -frustumSize * aspect / 2,
    frustumSize * aspect / 2,
    frustumSize / 2,
    -frustumSize / 2,
    -2000,
    5000
  );
  orthoCamera.position.set(160, 140, 200);

  // Perspective Camera (Optional toggle)
  perspCamera = new THREE.PerspectiveCamera(45, aspect, 1, 3000);
  perspCamera.position.set(160, 140, 200);

  // Active Camera
  camera = isOrthographic ? orthoCamera : perspCamera;
  window.camera = camera;
  window.isOrthographic = isOrthographic;
  window.setCameraMode = setCameraMode;
  window.setCameraView = setCameraView;
  window.state = state;

  // Renderer
  renderer = new THREE.WebGLRenderer({
    canvas: document.getElementById('three-canvas'),
    antialias: true,
    alpha: true
  });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;

  // Controls
  if (typeof THREE.OrbitControls !== 'undefined') {
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 20;
    controls.maxDistance = 1500;
    controls.target.set(0, 0, 0);
  }

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
  scene.add(ambientLight);

  const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight1.position.set(150, 250, 150);
  scene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0x38bdf8, 0.4);
  dirLight2.position.set(-150, -100, -150);
  scene.add(dirLight2);

  // Grid Helper (Ground plane at bottom of wheel)
  gridHelper = new THREE.GridHelper(300, 30, 0x334155, 0x1e293b);
  gridHelper.position.y = -state.wheel_radius_mm;
  scene.add(gridHelper);

  // Axes Helper (X=Red, Y=Green, Z=Blue)
  axesHelper = new THREE.AxesHelper(60);
  scene.add(axesHelper);

  // Wheel Group Container
  wheelGroup = new THREE.Group();
  scene.add(wheelGroup);

  // Raycaster & Mouse for hover interaction
  raycaster = new THREE.Raycaster();
  mouse = new THREE.Vector2();

  window.addEventListener('resize', onWindowResize);
  const canvas = renderer.domElement;
  canvas.addEventListener('mousemove', onMouseMove);
  canvas.addEventListener('click', onCanvasClick);

  setTimeout(onWindowResize, 60);
  setTimeout(onWindowResize, 250);

  animate();
}

function onWindowResize() {
  const container = document.getElementById('viewport-container');
  if (!container || !renderer) return;
  const width = container.clientWidth || 800;
  const height = container.clientHeight || 500;
  const aspect = width / height;

  frustumSize = Math.max(160, state.wheel_radius_mm * 2.8);

  if (orthoCamera) {
    orthoCamera.left = -frustumSize * aspect / 2;
    orthoCamera.right = frustumSize * aspect / 2;
    orthoCamera.top = frustumSize / 2;
    orthoCamera.bottom = -frustumSize / 2;
    orthoCamera.updateProjectionMatrix();
  }

  if (perspCamera) {
    perspCamera.aspect = aspect;
    perspCamera.updateProjectionMatrix();
  }

  renderer.setSize(width, height);
}

function animate() {
  animationFrameId = requestAnimationFrame(animate);
  if (state.display.autoRotate && wheelGroup) {
    wheelGroup.rotation.y += 0.005;
  }
  controls.update();
  renderer.render(scene, camera);
}

/* -------------------------------------------------------------
 * 2. 3D Model Building
 * ------------------------------------------------------------- */
function updateThreeScene(data) {
  if (!data || !wheelGroup) return;

  // Clear existing rollers and hub
  while (wheelGroup.children.length > 0) {
    const obj = wheelGroup.children[0];
    wheelGroup.remove(obj);
    if (obj.geometry) obj.geometry.dispose();
    if (obj.material) {
      if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
      else obj.material.dispose();
    }
  }
  rollerMeshes = [];
  arrowHelpers = [];

  const wheelRadiusMm = state.wheel_radius_mm;
  const tangentRadiusMm = state.tangent_radius_mm;
  const hubRadiusMm = Math.max(1, wheelRadiusMm - tangentRadiusMm * 1.4);

  // Update ground grid position
  if (gridHelper) {
    gridHelper.position.y = -wheelRadiusMm;
  }

  // Calculate wheel axial thickness based on layers
  let minOffset = 0, maxOffset = 0;
  state.layers.forEach(l => {
    minOffset = Math.min(minOffset, l.offset_mm);
    maxOffset = Math.max(maxOffset, l.offset_mm);
  });
  const hubWidth = Math.max(tangentRadiusMm * 2.2, (maxOffset - minOffset) + tangentRadiusMm * 2);

  // 1. Central Wheel Hub (Cylinder facing Y axis)
  if (state.display.showHub) {
    const hubGeometry = new THREE.CylinderGeometry(hubRadiusMm, hubRadiusMm, hubWidth, 48);
    // Cylinder is aligned along Y by default in Three.js
    const hubMaterial = new THREE.MeshStandardMaterial({
      color: 0x1e3a8a,
      roughness: 0.35,
      metalness: 0.65,
      transparent: true,
      opacity: 0.65
    });
    hubMesh = new THREE.Mesh(hubGeometry, hubMaterial);
    hubMesh.position.set(0, (minOffset + maxOffset) / 2, 0);
    wheelGroup.add(hubMesh);

    // Rim outer circle guide wireframe
    const rimRadius = wheelRadiusMm - tangentRadiusMm;
    const rimCurve = new THREE.EllipseCurve(0, 0, rimRadius, rimRadius, 0, 2 * Math.PI, false, 0);
    const rimPoints = rimCurve.getPoints(64);
    const rimGeom = new THREE.BufferGeometry().setFromPoints(rimPoints.map(p => new THREE.Vector3(p.x, 0, p.y)));
    const rimMat = new THREE.LineDashedMaterial({ color: 0x38bdf8, dashSize: 4, gapSize: 2, transparent: true, opacity: 0.4 });
    const rimLine = new THREE.LineLoop(rimGeom, rimMat);
    rimLine.computeLineDistances();
    wheelGroup.add(rimLine);

    // Center Axle Bore
    const boreGeom = new THREE.CylinderGeometry(hubRadiusMm * 0.2, hubRadiusMm * 0.2, hubWidth + 2, 24);
    const boreMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.8 });
    const boreMesh = new THREE.Mesh(boreGeom, boreMat);
    boreMesh.position.copy(hubMesh.position);
    wheelGroup.add(boreMesh);
  }

  // 2. Rollers with Compound Sub-colliders (Paper models C, S, O or basic)
  const defaultSubs = getColliderSubelementsJS(
    state.roller_shape,
    state.wheel_radius_mm,
    state.tangent_radius_mm,
    state.roller_length_mm
  );

  data.roller_data.forEach(r => {
    // Note: positions are in meters in backend, convert to mm for Three.js
    const posX = r.position[0] * 1000;
    const posY = r.position[1] * 1000;
    const posZ = r.position[2] * 1000;
    const rollerCenter = new THREE.Vector3(posX, posY, posZ);

    const layerIdx = r.layer || 0;
    const colorHex = LAYER_COLORS[layerIdx % LAYER_COLORS.length];

    const spinVector = r.world_axis || r.axis;
    const dir = new THREE.Vector3(spinVector[0], spinVector[1], spinVector[2]).normalize();

    // Solid roller material
    const rollerMat = new THREE.MeshStandardMaterial({
      color: colorHex,
      roughness: 0.35,
      metalness: 0.4
    });

    const wireMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      wireframe: true,
      transparent: true,
      opacity: 0.3
    });

    const subsToRender = (r.subelements && r.subelements.length > 0)
      ? r.subelements.map(s => ({
          type: s.type,
          u_mm: s.u * 1000,
          radius_mm: s.radius * 1000,
          length_mm: s.length ? s.length * 1000 : 0
        }))
      : defaultSubs;

    subsToRender.forEach(sub => {
      const subPos = rollerCenter.clone().addScaledVector(dir, sub.u_mm);
      let mesh, wireMesh;

      if (sub.type === 'cylinder') {
        const geom = new THREE.CylinderGeometry(sub.radius_mm, sub.radius_mm, sub.length_mm, 20);
        mesh = new THREE.Mesh(geom, rollerMat);
        mesh.position.copy(subPos);
        mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);

        if (state.display.showWireframe) {
          const wGeom = new THREE.CylinderGeometry(sub.radius_mm * 1.01, sub.radius_mm * 1.01, sub.length_mm * 1.01, 12);
          wireMesh = new THREE.Mesh(wGeom, wireMat);
          wireMesh.position.copy(subPos);
          wireMesh.quaternion.copy(mesh.quaternion);
        }
      } else {
        const geom = new THREE.SphereGeometry(sub.radius_mm, 18, 14);
        mesh = new THREE.Mesh(geom, rollerMat);
        mesh.position.copy(subPos);

        if (state.display.showWireframe) {
          const wGeom = new THREE.SphereGeometry(sub.radius_mm * 1.01, 10, 8);
          wireMesh = new THREE.Mesh(wGeom, wireMat);
          wireMesh.position.copy(subPos);
        }
      }

      mesh.userData = { rollerData: r, subelement: sub };
      wheelGroup.add(mesh);
      rollerMeshes.push(mesh);

      if (wireMesh) {
        wheelGroup.add(wireMesh);
      }
    });

    // Rotation Axis Arrow (uses true physical spin axis in 3D world space)
    if (state.display.showArrows && spinVector) {
      const arrowLength = tangentRadiusMm * 2.2;
      const arrowHelper = new THREE.ArrowHelper(dir, rollerCenter, arrowLength, 0xef4444, tangentRadiusMm * 0.7, tangentRadiusMm * 0.4);
      wheelGroup.add(arrowHelper);
      arrowHelpers.push(arrowHelper);

      // Add reverse arrow head to show bi-directional rotation axis
      const revDir = dir.clone().negate();
      const revArrow = new THREE.ArrowHelper(revDir, rollerCenter, arrowLength, 0xef4444, tangentRadiusMm * 0.7, tangentRadiusMm * 0.4);
      wheelGroup.add(revArrow);
      arrowHelpers.push(revArrow);
    }
  });

  // Toggle Visibility helpers
  if (gridHelper) gridHelper.visible = state.display.showGrid;
  if (axesHelper) axesHelper.visible = state.display.showAxes;
}

/* -------------------------------------------------------------
 * 3. Mouse Interaction & Selection
 * ------------------------------------------------------------- */
function onMouseMove(event) {
  const container = document.getElementById('viewport-container');
  const rect = container.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(rollerMeshes);
  const tooltip = document.getElementById('roller-tooltip');

  if (intersects.length > 0) {
    const hit = intersects[0].object;
    const rData = hit.userData.rollerData;
    if (rData) {
      tooltip.style.display = 'block';
      tooltip.style.left = `${event.clientX - rect.left + 15}px`;
      tooltip.style.top = `${event.clientY - rect.top + 15}px`;
      tooltip.innerHTML = `
        <div class="font-bold text-cyan-400">Roller #${rData.id} (Layer ${rData.layer + 1})</div>
        <div>Model: <span class="text-cyan-300 font-semibold">${(state.roller_shape || 'o11').toUpperCase()}</span> (${rData.subelements ? rData.subelements.length : 1} colliders)</div>
        <div>Theta: <span class="text-white">${rData.theta_deg.toFixed(1)}°</span></div>
        <div>Pos (mm): <span class="text-white">[${(rData.position[0]*1000).toFixed(1)}, ${(rData.position[1]*1000).toFixed(1)}, ${(rData.position[2]*1000).toFixed(1)}]</span></div>
        <div>Spin Axis: <span class="text-white">[${(rData.world_axis || rData.axis).map(v => v.toFixed(3)).join(', ')}]</span></div>
        <div>URDF Axis: <span class="text-slate-400">[${rData.axis.map(v => v.toFixed(3)).join(', ')}]</span></div>
      `;
      container.style.cursor = 'pointer';
      return;
    }
  }

  tooltip.style.display = 'none';
  container.style.cursor = 'default';
}

function onCanvasClick() {
  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObjects(rollerMeshes);
  if (intersects.length > 0) {
    const hit = intersects[0].object;
    const rData = hit.userData.rollerData;
    if (rData) {
      selectRoller(rData.id);
    }
  }
}

function selectRoller(id) {
  state.selectedRollerId = id;

  // Highlight 3D mesh
  rollerMeshes.forEach(mesh => {
    const rData = mesh.userData.rollerData;
    if (rData.id === id) {
      mesh.material.emissive = new THREE.Color(0x38bdf8);
      mesh.material.emissiveIntensity = 0.6;
    } else {
      mesh.material.emissive = new THREE.Color(0x000000);
      mesh.material.emissiveIntensity = 0.0;
    }
  });

  // Switch to table tab and highlight row
  switchTab('table');
  const rows = document.querySelectorAll('.roller-table tbody tr');
  rows.forEach(r => {
    if (parseInt(r.getAttribute('data-id')) === id) {
      r.classList.add('selected');
      r.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
      r.classList.remove('selected');
    }
  });
}

/* -------------------------------------------------------------
 * 4. API Calls & Reactive Compute
 * ------------------------------------------------------------- */
let computeTimeout = null;
function triggerCompute() {
  if (computeTimeout) clearTimeout(computeTimeout);
  computeTimeout = setTimeout(performCompute, 60);
}

async function performCompute() {
  const payload = {
    wheel_radius: state.wheel_radius_mm / 1000.0,
    tangent_radius: state.tangent_radius_mm / 1000.0,
    roller_shape: state.roller_shape,
    collider_type: state.roller_shape,
    roller_length: state.roller_length_mm / 1000.0,
    roller_weight: state.roller_weight_kg,
    roller_method: state.roller_method,
    prefix: state.prefix,
    wheel_name: state.wheel_name,
    layers: state.layers.map(l => ({
      offset: l.offset_mm / 1000.0,
      angle: l.angle_deg,
      rollers: parseInt(l.rollers)
    }))
  };

  try {
    const res = await fetch('/api/compute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      state.currentData = data;
      updateThreeScene(data);
      updateMetricsHUD(data.metrics);
      updateTabOutputs(data);
    } else {
      console.error("Compute error:", data.error);
    }
  } catch (err) {
    console.error("Fetch error:", err);
  }
}

function updateMetricsHUD(metrics) {
  if (!metrics) return;
  document.getElementById('hud-total-rollers').innerText = metrics.total_rollers;
  document.getElementById('hud-outer-dia').innerText = `${metrics.outer_diameter_mm} mm`;
  document.getElementById('hud-hub-dia').innerText = `${metrics.hub_diameter_mm} mm`;
  document.getElementById('hud-roller-dia').innerText = `${metrics.roller_diameter_mm} mm`;
  document.getElementById('hud-total-mass').innerText = `${(metrics.total_roller_mass_kg * 1000).toFixed(1)} g`;
}

function updateTabOutputs(data) {
  document.getElementById('urdf-snippet-output').value = data.urdf_snippet || '';
  document.getElementById('full-urdf-output').value = data.full_urdf || '';
  document.getElementById('yaml-output').value = data.yaml_content || '';
  renderRollerTable(data.roller_data);
}

function renderRollerTable(rollerData) {
  const tbody = document.getElementById('roller-table-body');
  if (!tbody || !rollerData) return;
  tbody.innerHTML = '';

  rollerData.forEach(r => {
    const tr = document.createElement('tr');
    tr.setAttribute('data-id', r.id);
    if (state.selectedRollerId === r.id) tr.classList.add('selected');

    const layerClass = `layer-badge-${(r.layer || 0) % 6}`;

    tr.innerHTML = `
      <td class="px-3 py-1.5 font-mono text-cyan-400">#${r.id}</td>
      <td class="px-3 py-1.5">
        <span class="inline-block px-1.5 py-0.5 rounded text-xs text-white ${layerClass}">L${r.layer + 1}</span>
      </td>
      <td class="px-3 py-1.5 font-mono">${r.theta_deg.toFixed(1)}°</td>
      <td class="px-3 py-1.5 font-mono text-xs">[${r.position.map(v => v.toFixed(4)).join(', ')}]</td>
      <td class="px-3 py-1.5 font-mono text-xs">[${r.rpy.map(v => v.toFixed(4)).join(', ')}]</td>
      <td class="px-3 py-1.5 font-mono text-xs text-slate-300">[${r.axis.map(v => v.toFixed(3)).join(', ')}]</td>
    `;

    tr.addEventListener('click', () => {
      selectRoller(r.id);
    });

    tbody.appendChild(tr);
  });
}

/* -------------------------------------------------------------
 * 5. UI Layer Management
 * ------------------------------------------------------------- */
function renderLayersUI() {
  const container = document.getElementById('layers-container');
  if (!container) return;
  container.innerHTML = '';

  state.layers.forEach((layer, idx) => {
    const card = document.createElement('div');
    card.className = 'p-3 bg-slate-800/80 border border-slate-700 rounded-lg space-y-2 relative';

    const colorHex = LAYER_COLORS[idx % LAYER_COLORS.length].toString(16).padStart(6, '0');

    card.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="w-3 h-3 rounded-full" style="background-color: #${colorHex}"></span>
          <span class="font-semibold text-xs text-slate-200">Layer ${idx + 1}</span>
        </div>
        <div class="flex space-x-1">
          ${state.layers.length > 1 ? `
          <button class="p-1 hover:bg-rose-500/20 text-rose-400 rounded transition text-xs delete-layer-btn" data-index="${idx}" title="Remove layer">
            ✕
          </button>` : ''}
        </div>
      </div>

      <div class="grid grid-cols-3 gap-2 text-xs">
        <div>
          <label class="text-slate-400 block mb-1">Offset Y (mm)</label>
          <input type="number" step="0.5" class="input-number-compact layer-offset" data-index="${idx}" value="${layer.offset_mm}">
        </div>
        <div>
          <label class="text-slate-400 block mb-1">Angle Offset (°)</label>
          <input type="number" step="1.0" class="input-number-compact layer-angle" data-index="${idx}" value="${layer.angle_deg}">
        </div>
        <div>
          <label class="text-slate-400 block mb-1">Rollers</label>
          <input type="number" min="2" max="64" step="1" class="input-number-compact layer-rollers" data-index="${idx}" value="${layer.rollers}">
        </div>
      </div>
    `;

    container.appendChild(card);
  });

  // Attach event listeners to layer inputs
  document.querySelectorAll('.layer-offset').forEach(input => {
    input.addEventListener('input', (e) => {
      const idx = parseInt(e.target.dataset.index);
      state.layers[idx].offset_mm = parseFloat(e.target.value) || 0.0;
      triggerCompute();
    });
  });

  document.querySelectorAll('.layer-angle').forEach(input => {
    input.addEventListener('input', (e) => {
      const idx = parseInt(e.target.dataset.index);
      state.layers[idx].angle_deg = parseFloat(e.target.value) || 0.0;
      triggerCompute();
    });
  });

  document.querySelectorAll('.layer-rollers').forEach(input => {
    input.addEventListener('input', (e) => {
      const idx = parseInt(e.target.dataset.index);
      state.layers[idx].rollers = parseInt(e.target.value) || 8;
      triggerCompute();
    });
  });

  document.querySelectorAll('.delete-layer-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const idx = parseInt(e.target.dataset.index);
      if (state.layers.length > 1) {
        state.layers.splice(idx, 1);
        renderLayersUI();
        triggerCompute();
      }
    });
  });
}

function addLayer() {
  const lastLayer = state.layers[state.layers.length - 1];
  const newOffset = lastLayer ? -lastLayer.offset_mm : 10.0;
  const newAngle = lastLayer ? (lastLayer.angle_deg + 22.5) % 360 : 0.0;
  const rollers = lastLayer ? lastLayer.rollers : 8;

  state.layers.push({
    offset_mm: Math.round(newOffset * 10) / 10,
    angle_deg: Math.round(newAngle * 10) / 10,
    rollers: rollers
  });

  renderLayersUI();
  triggerCompute();
}

/* -------------------------------------------------------------
 * 6. Camera View Controls
 * ------------------------------------------------------------- */
function setCameraView(view) {
  if (!camera || !controls) return;
  const dist = state.wheel_radius_mm * 4;

  switch (view) {
    case 'front': // Looking directly down Y axis at X-Z plane (wheel face)
      camera.position.set(0, dist, 0.0001);
      camera.up.set(0, 0, 1);
      break;
    case 'side': // Looking down X axis at Y-Z plane (side profile / layer thickness)
      camera.position.set(dist, 0, 0.0001);
      camera.up.set(0, 0, 1);
      break;
    case 'top': // Looking down Z axis at X-Y plane
      camera.position.set(0, 0.0001, dist);
      camera.up.set(0, 1, 0);
      break;
    case 'iso':
    default:
      camera.position.set(dist * 0.7, dist * 0.6, dist * 0.8);
      camera.up.set(0, 1, 0);
      break;
  }

  controls.target.set(0, 0, 0);
  if (isOrthographic && orthoCamera) {
    orthoCamera.zoom = 1;
    orthoCamera.updateProjectionMatrix();
  }
  controls.update();
}

function toggleCameraMode() {
  setCameraMode(!isOrthographic);
}

function setCameraMode(ortho) {
  isOrthographic = ortho;
  const oldPos = camera.position.clone();
  const oldUp = camera.up.clone();
  const oldTarget = controls.target.clone();

  camera = isOrthographic ? orthoCamera : perspCamera;
  window.camera = camera;
  window.isOrthographic = isOrthographic;
  camera.position.copy(oldPos);
  camera.up.copy(oldUp);
  controls.object = camera;
  controls.target.copy(oldTarget);

  onWindowResize();
  controls.update();

  const modeBtn = document.getElementById('cam-mode');
  if (modeBtn) {
    modeBtn.textContent = isOrthographic ? 'Ortho' : 'Persp';
    modeBtn.title = isOrthographic 
      ? 'Current: Orthographic (CAD parallel view). Click to switch to Perspective' 
      : 'Current: Perspective (Natural depth view). Click to switch to Orthographic';
    modeBtn.className = isOrthographic 
      ? 'px-2 py-0.5 bg-cyan-950 text-cyan-400 border border-cyan-800 rounded font-semibold transition'
      : 'px-2 py-0.5 hover:bg-slate-800 text-slate-400 rounded transition';
  }
}

/* -------------------------------------------------------------
 * 7. Event Listeners & Preset Loading
 * ------------------------------------------------------------- */
function initEventListeners() {
  // Main parameters
  const wheelRadiusInput = document.getElementById('wheel-radius');
  const tangentRadiusInput = document.getElementById('tangent-radius');
  const rollerWeightInput = document.getElementById('roller-weight');
  const rollerMethodSelect = document.getElementById('roller-method');
  const urdfPrefixInput = document.getElementById('urdf-prefix');

  const rollerShapeSelect = document.getElementById('roller-shape');
  const rollerLengthInput = document.getElementById('roller-length');
  const rollerLengthContainer = document.getElementById('roller-length-container');

  wheelRadiusInput.value = state.wheel_radius_mm;
  tangentRadiusInput.value = state.tangent_radius_mm;
  rollerShapeSelect.value = state.roller_shape;
  rollerLengthInput.value = state.roller_length_mm;
  rollerWeightInput.value = state.roller_weight_kg;
  rollerMethodSelect.value = state.roller_method;
  urdfPrefixInput.value = state.prefix;

  wheelRadiusInput.addEventListener('input', (e) => {
    state.wheel_radius_mm = parseFloat(e.target.value) || 50;
    triggerCompute();
  });

  tangentRadiusInput.addEventListener('input', (e) => {
    state.tangent_radius_mm = parseFloat(e.target.value) || 8;
    triggerCompute();
  });

  rollerShapeSelect.addEventListener('change', (e) => {
    state.roller_shape = e.target.value;
    if (state.roller_shape === 'sphere') {
      rollerLengthContainer.style.opacity = '0.5';
    } else {
      rollerLengthContainer.style.opacity = '1';
      rollerLengthContainer.style.pointerEvents = 'auto';
    }
    triggerCompute();
  });

  rollerLengthInput.addEventListener('input', (e) => {
    state.roller_length_mm = parseFloat(e.target.value) || 15;
    triggerCompute();
  });

  rollerWeightInput.addEventListener('input', (e) => {
    state.roller_weight_kg = parseFloat(e.target.value) || 0.01;
    triggerCompute();
  });

  rollerMethodSelect.addEventListener('change', (e) => {
    state.roller_method = e.target.value;
    triggerCompute();
  });

  urdfPrefixInput.addEventListener('input', (e) => {
    state.prefix = e.target.value;
    triggerCompute();
  });

  document.getElementById('add-layer-btn').addEventListener('click', addLayer);

  // Display toggles
  document.getElementById('toggle-hub').addEventListener('change', (e) => {
    state.display.showHub = e.target.checked;
    updateThreeScene(state.currentData);
  });
  document.getElementById('toggle-wireframe').addEventListener('change', (e) => {
    state.display.showWireframe = e.target.checked;
    updateThreeScene(state.currentData);
  });
  document.getElementById('toggle-arrows').addEventListener('change', (e) => {
    state.display.showArrows = e.target.checked;
    updateThreeScene(state.currentData);
  });
  document.getElementById('toggle-grid').addEventListener('change', (e) => {
    state.display.showGrid = e.target.checked;
    if (gridHelper) gridHelper.visible = e.target.checked;
  });
  document.getElementById('toggle-axes').addEventListener('change', (e) => {
    state.display.showAxes = e.target.checked;
    if (axesHelper) axesHelper.visible = e.target.checked;
  });
  document.getElementById('toggle-autorotate').addEventListener('change', (e) => {
    state.display.autoRotate = e.target.checked;
  });

  // Camera buttons
  document.getElementById('cam-iso').addEventListener('click', () => setCameraView('iso'));
  document.getElementById('cam-front').addEventListener('click', () => setCameraView('front'));
  document.getElementById('cam-side').addEventListener('click', () => setCameraView('side'));
  document.getElementById('cam-top').addEventListener('click', () => setCameraView('top'));
  document.getElementById('cam-reset').addEventListener('click', () => setCameraView('iso'));
  const camModeBtn = document.getElementById('cam-mode');
  if (camModeBtn) {
    camModeBtn.addEventListener('click', toggleCameraMode);
  }

  // Preset selector
  document.getElementById('preset-selector').addEventListener('change', (e) => {
    loadPreset(e.target.value);
  });

  // Saved configs selector
  document.getElementById('saved-config-selector').addEventListener('change', (e) => {
    if (e.target.value) {
      loadSavedConfig(e.target.value);
    }
  });

  // Action Buttons
  document.getElementById('btn-save-server').addEventListener('click', saveToServer);
  document.getElementById('btn-copy-urdf').addEventListener('click', () => copyToClipboard('urdf-snippet-output'));
  document.getElementById('btn-download-urdf').addEventListener('click', downloadURDF);
  document.getElementById('btn-copy-yaml').addEventListener('click', () => copyToClipboard('yaml-output'));
  document.getElementById('btn-download-yaml').addEventListener('click', downloadYAML);
  document.getElementById('btn-export-csv').addEventListener('click', exportTableCSV);

  // File Upload
  const fileInput = document.getElementById('yaml-file-input');
  fileInput.addEventListener('change', handleFileUpload);
}

async function loadPresetsList() {
  try {
    const res = await fetch('/api/presets');
    if (res.ok) {
      const serverPresets = await res.json();
      presetsData = Object.assign({}, DEFAULT_PRESETS, serverPresets);
      populatePresetsDropdown(presetsData);
    }
  } catch (err) {
    console.warn("Could not fetch server presets, using built-in defaults:", err);
  }
}

function loadPreset(key) {
  const p = presetsData[key];
  if (!p) return;

  state.wheel_radius_mm = p.wheel_radius * 1000;
  state.tangent_radius_mm = p.tangent_radius * 1000;
  state.roller_shape = p.collider_type || p.roller_shape || 'o11';
  state.roller_length_mm = (p.roller_length || (p.tangent_radius * 2.5)) * 1000;
  state.roller_weight_kg = p.roller_weight;
  state.roller_method = p.roller_method;

  document.getElementById('wheel-radius').value = state.wheel_radius_mm;
  document.getElementById('tangent-radius').value = state.tangent_radius_mm;
  document.getElementById('roller-shape').value = state.roller_shape;
  document.getElementById('roller-length').value = state.roller_length_mm;
  document.getElementById('roller-weight').value = state.roller_weight_kg;
  document.getElementById('roller-method').value = state.roller_method;

  const rlenContainer = document.getElementById('roller-length-container');
  if (rlenContainer) {
    rlenContainer.style.opacity = (state.roller_shape === 'sphere') ? '0.5' : '1';
  }

  state.layers = p.layers.map(l => ({
    offset_mm: l.offset * 1000,
    angle_deg: l.angle,
    rollers: l.rollers || p.global_rollers_per_layer || 8
  }));

  renderLayersUI();
  triggerCompute();
}

async function loadSavedConfigsList() {
  try {
    const res = await fetch('/api/saved-configs');
    const data = await res.json();
    const select = document.getElementById('saved-config-selector');
    select.innerHTML = '<option value="">-- Load from wheel_config/ --</option>';
    data.files.forEach(f => {
      const opt = document.createElement('option');
      opt.value = f.filename;
      opt.textContent = f.filename;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error("Failed to load saved configs", err);
  }
}

async function loadSavedConfig(filename) {
  try {
    const res = await fetch(`/api/saved-configs/${filename}`);
    const data = await res.json();
    applyParsedData(data);
  } catch (err) {
    alert("Error loading config: " + err.message);
  }
}

function applyParsedData(data) {
  if (!data || !data.config) return;
  const cfg = data.config;

  state.wheel_radius_mm = cfg.wheel_radius * 1000;
  state.tangent_radius_mm = cfg.tangent_radius * 1000;
  state.roller_shape = cfg.roller_shape || 'sphere';
  state.roller_length_mm = (cfg.roller_length || (cfg.tangent_radius * 2.5)) * 1000;
  state.roller_weight_kg = cfg.roller_weight;
  state.roller_method = cfg.roller_method || 'axis';

  document.getElementById('wheel-radius').value = state.wheel_radius_mm;
  document.getElementById('tangent-radius').value = state.tangent_radius_mm;
  document.getElementById('roller-shape').value = state.roller_shape;
  document.getElementById('roller-length').value = state.roller_length_mm;
  document.getElementById('roller-weight').value = state.roller_weight_kg;
  document.getElementById('roller-method').value = state.roller_method;

  if (data.layers && data.layers.length > 0) {
    state.layers = data.layers.map(l => ({
      offset_mm: l.offset * 1000,
      angle_deg: l.angle,
      rollers: l.rollers
    }));
  }

  renderLayersUI();
  state.currentData = data;
  updateThreeScene(data);
  updateMetricsHUD(data.metrics);
  updateTabOutputs(data);
}

async function handleFileUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/upload-yaml', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      applyParsedData(data);
      alert(`Loaded ${file.name} successfully!`);
    } else {
      alert("Error parsing file: " + data.error);
    }
  } catch (err) {
    alert("Upload failed: " + err.message);
  }
}

async function saveToServer() {
  if (!state.currentData) return;
  const yamlFilename = prompt("Enter YAML filename to save into wheel_config/:", "omni_wheel_config.yml");
  if (!yamlFilename) return;

  try {
    const res = await fetch('/api/save-files', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        yaml_content: state.currentData.yaml_content,
        urdf_content: state.currentData.urdf_snippet,
        yaml_filename: yamlFilename,
        urdf_filename: "output.txt"
      })
    });
    const result = await res.json();
    if (result.success) {
      alert(`Saved successfully!\nYAML: ${result.saved_yaml}\nURDF: ${result.saved_urdf}`);
      loadSavedConfigsList();
    } else {
      alert("Save failed: " + result.error);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

/* -------------------------------------------------------------
 * 9. Tab Management & Exports
 * ------------------------------------------------------------- */
function switchTab(tabName) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.dataset.tab === tabName) {
      btn.classList.add('border-cyan-400', 'text-cyan-400');
      btn.classList.remove('border-transparent', 'text-slate-400');
    } else {
      btn.classList.remove('border-cyan-400', 'text-cyan-400');
      btn.classList.add('border-transparent', 'text-slate-400');
    }
  });

  document.querySelectorAll('.tab-pane').forEach(pane => {
    if (pane.id === `tab-${tabName}`) {
      pane.classList.remove('hidden');
    } else {
      pane.classList.add('hidden');
    }
  });
}

function copyToClipboard(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  navigator.clipboard.writeText(el.value).then(() => {
    alert("Copied to clipboard!");
  });
}

function downloadURDF() {
  if (!state.currentData) return;
  const blob = new Blob([state.currentData.urdf_snippet], { type: 'text/xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'omni_wheel_collision.xacro';
  a.click();
  URL.revokeObjectURL(url);
}

function downloadYAML() {
  if (!state.currentData) return;
  const blob = new Blob([state.currentData.yaml_content], { type: 'text/yaml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'omni_wheel_config.yml';
  a.click();
  URL.revokeObjectURL(url);
}

function exportTableCSV() {
  if (!state.currentData || !state.currentData.roller_data) return;
  let csv = "ID,Layer,Theta_deg,Pos_X,Pos_Y,Pos_Z,RPY_R,RPY_P,RPY_Y,Axis_X,Axis_Y,Axis_Z\n";
  state.currentData.roller_data.forEach(r => {
    csv += `${r.id},${r.layer + 1},${r.theta_deg},${r.position[0]},${r.position[1]},${r.position[2]},${r.rpy[0]},${r.rpy[1]},${r.rpy[2]},${r.axis[0]},${r.axis[1]},${r.axis[2]}\n`;
  });
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'roller_collision_positions.csv';
  a.click();
  URL.revokeObjectURL(url);
}

// Expose switchTab globally for inline onclick handlers
window.switchTab = switchTab;
