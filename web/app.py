import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from core.omni_generator import (
    calculate_roller_positions_from_layers,
    compute_roller_data,
    generate_urdf_snippet,
    generate_full_standalone_urdf,
    generate_yaml_string,
    PRESETS
)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = WORKSPACE_ROOT / "wheel_config"
STATIC_DIR = Path(__file__).resolve().parent / "static"

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="Omniwheel Collision URDF Generator",
    description="Interactive Web-based 3D visualizer and URDF generator for omni-directional wheels",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.middleware("http")
async def add_cache_control_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



class LayerModel(BaseModel):
    offset: float = Field(..., description="Y-axis offset in meters")
    angle: float = Field(0.0, description="Angular offset in degrees")
    rollers: int = Field(8, description="Number of rollers in this layer")


class ComputeRequest(BaseModel):
    wheel_radius: float = Field(0.050, gt=0, description="Wheel radius in meters")
    tangent_radius: float = Field(0.008, gt=0, description="Roller collision radius in meters")
    roller_shape: str = Field("sphere", pattern="^(sphere|cylinder)$", description="Roller collision shape")
    roller_length: Optional[float] = Field(None, gt=0, description="Roller cylinder length in meters")
    roller_weight: float = Field(0.010, gt=0, description="Roller mass in kg")
    roller_method: str = Field("axis", pattern="^(axis|rotation)$", description="Orientation method")
    layers: List[LayerModel] = Field(default_factory=list)
    prefix: str = Field("${prefix}", description="URDF prefix parameter")
    wheel_name: str = Field("omni_wheel", description="Standalone wheel name")
    custom_positions: Optional[List[List[Any]]] = None


class SaveRequest(BaseModel):
    yaml_content: str
    urdf_content: str
    yaml_filename: str = "omni_wheel_config.yml"
    urdf_filename: str = "output.txt"


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/presets")
async def get_presets():
    return JSONResponse(PRESETS)


@app.get("/api/saved-configs")
async def get_saved_configs():
    files = []
    if CONFIG_DIR.exists():
        for f in CONFIG_DIR.glob("*.y*ml"):
            files.append({
                "filename": f.name,
                "path": str(f.relative_to(WORKSPACE_ROOT)),
                "size": f.stat().st_size
            })
    return JSONResponse({"files": sorted(files, key=lambda x: x["filename"])})


@app.get("/api/saved-configs/{filename}")
async def load_saved_config(filename: str):
    file_path = CONFIG_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            config = yaml.safe_load(content)
        return await process_parsed_config(config, raw_yaml=content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing YAML: {str(e)}")


@app.post("/api/compute")
async def compute(req: ComputeRequest):
    try:
        actual_len = req.roller_length or round(req.tangent_radius * 2.5, 4)
        if req.custom_positions and len(req.custom_positions) > 0:
            config = {
                'wheel_radius': req.wheel_radius,
                'tangent_radius': req.tangent_radius,
                'roller_shape': req.roller_shape,
                'roller_length': actual_len,
                'roller_weight': req.roller_weight,
                'roller_count': len(req.custom_positions),
                'roller_method': req.roller_method,
                'position': req.custom_positions,
                'layer_info': [0] * len(req.custom_positions)
            }
        else:
            layers_dict = [layer.dict() for layer in req.layers]
            config = calculate_roller_positions_from_layers(
                wheel_radius=req.wheel_radius,
                tangent_radius=req.tangent_radius,
                roller_weight=req.roller_weight,
                roller_method=req.roller_method,
                layers=layers_dict,
                roller_shape=req.roller_shape,
                roller_length=actual_len
            )

        roller_data = compute_roller_data(config)
        urdf_snippet = generate_urdf_snippet(config, roller_data, prefix=req.prefix)
        full_urdf = generate_full_standalone_urdf(config, roller_data, wheel_name=req.wheel_name)
        yaml_content = generate_yaml_string(config)

        total_roller_mass = round(config['roller_count'] * config['roller_weight'], 4)
        outer_diameter = round(config['wheel_radius'] * 2 * 1000, 2)  # mm
        hub_diameter = round((config['wheel_radius'] - config['tangent_radius']) * 2 * 1000, 2)  # mm

        return {
            "success": True,
            "config": config,
            "roller_data": roller_data,
            "urdf_snippet": urdf_snippet,
            "full_urdf": full_urdf,
            "yaml_content": yaml_content,
            "metrics": {
                "total_rollers": config['roller_count'],
                "layers_count": len(req.layers) if req.layers else 1,
                "outer_diameter_mm": outer_diameter,
                "hub_diameter_mm": hub_diameter,
                "roller_diameter_mm": round(config['tangent_radius'] * 2 * 1000, 2),
                "total_roller_mass_kg": total_roller_mass
            }
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


async def process_parsed_config(config: Dict[str, Any], raw_yaml: str = ""):
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="Invalid YAML: Root must be a dictionary")

    wheel_radius = float(config.get('wheel_radius', 0.05))
    tangent_radius = float(config.get('tangent_radius', 0.008))
    roller_weight = float(config.get('roller_weight', 0.01))
    roller_method = config.get('roller_method', 'axis')
    positions = config.get('position', [])

    # Infer layers from offset values
    offset_groups = {}
    for pos in positions:
        offset = round(float(pos[1]), 6)
        if offset not in offset_groups:
            offset_groups[offset] = []
        offset_groups[offset].append(float(pos[0]))

    layers = []
    layer_info = []
    sorted_offsets = sorted(offset_groups.keys())
    offset_to_layer_idx = {off: idx for idx, off in enumerate(sorted_offsets)}

    for off in sorted_offsets:
        thetas = sorted(offset_groups[off])
        angle_0 = thetas[0] if thetas else 0.0
        layers.append({
            "offset": off,
            "angle": round(angle_0, 2),
            "rollers": len(thetas)
        })

    for pos in positions:
        off = round(float(pos[1]), 6)
        layer_info.append(offset_to_layer_idx.get(off, 0))

    roller_shape = config.get('roller_shape', 'sphere')
    roller_length = float(config.get('roller_length', round(tangent_radius * 2.5, 4)))
    config['roller_shape'] = roller_shape
    config['roller_length'] = roller_length
    config['layer_info'] = layer_info
    config['roller_count'] = len(positions)
    roller_data = compute_roller_data(config)
    urdf_snippet = generate_urdf_snippet(config, roller_data)
    full_urdf = generate_full_standalone_urdf(config, roller_data)
    yaml_content = raw_yaml if raw_yaml else generate_yaml_string(config)

    return {
        "success": True,
        "roller_shape": roller_shape,
        "roller_length": roller_length,
        "config": config,
        "layers": layers,
        "roller_data": roller_data,
        "urdf_snippet": urdf_snippet,
        "full_urdf": full_urdf,
        "yaml_content": yaml_content,
        "metrics": {
            "total_rollers": len(positions),
            "layers_count": len(layers),
            "outer_diameter_mm": round(wheel_radius * 2 * 1000, 2),
            "hub_diameter_mm": round((wheel_radius - tangent_radius) * 2 * 1000, 2),
            "roller_diameter_mm": round(tangent_radius * 2 * 1000, 2),
            "total_roller_mass_kg": round(len(positions) * roller_weight, 4)
        }
    }


class ParseYamlRequest(BaseModel):
    yaml_text: str


@app.post("/api/parse-yaml")
async def parse_yaml(req: ParseYamlRequest):
    try:
        config = yaml.safe_load(req.yaml_text)
        return await process_parsed_config(config, raw_yaml=req.yaml_text)
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.post("/api/upload-yaml")
async def upload_yaml(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8")
        config = yaml.safe_load(text)
        return await process_parsed_config(config, raw_yaml=text)
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.post("/api/save-files")
async def save_files(req: SaveRequest):
    try:
        yaml_path = CONFIG_DIR / req.yaml_filename
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(req.yaml_content)

        urdf_path = WORKSPACE_ROOT / req.urdf_filename
        with open(urdf_path, "w", encoding="utf-8") as f:
            f.write(req.urdf_content)

        return {
            "success": True,
            "saved_yaml": str(yaml_path.relative_to(WORKSPACE_ROOT)),
            "saved_urdf": str(urdf_path.relative_to(WORKSPACE_ROOT))
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})
