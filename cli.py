#!/usr/bin/env python3
"""
Omniwheel Collision URDF Tools - Modern Unified CLI
Powered by core.omni_generator and web.app
"""

import os
import sys
import argparse
import yaml
from pathlib import Path

from core.omni_generator import (
    calculate_roller_positions_from_layers,
    compute_roller_data,
    generate_urdf_snippet,
    generate_full_standalone_urdf,
    generate_yaml_string,
    PRESETS
)

CONFIG_DIR = Path("wheel_config")
DEFAULT_CONFIG = CONFIG_DIR / "omni_wheel_config.yml"
EXAMPLE_CONFIG = CONFIG_DIR / "example.yaml"


def cmd_gui(args):
    """Launch the Web-based GUI visualizer serving docs/ statically."""
    import http.server
    import socketserver

    docs_dir = Path(__file__).resolve().parent / "docs"
    if not docs_dir.exists():
        print(f"❌ Error: docs/ directory not found at {docs_dir}")
        sys.exit(1)

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(docs_dir), **kw)

        def end_headers(self):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            super().end_headers()

        def log_message(self, format, *args):
            if "200 -" not in format % args and "304 -" not in format % args:
                super().log_message(format, *args)

    socketserver.TCPServer.allow_reuse_address = True
    display_host = "localhost" if args.host in ("0.0.0.0", "::") else args.host
    print(f"🚀 Starting Omniwheel Studio Web GUI on http://{display_host}:{args.port}")
    print(f"📁 Serving files from: {docs_dir}")
    print(f"✨ 100% Client-Side Progressive Web App (identical to GitHub Pages)")
    try:
        with socketserver.TCPServer((args.host, args.port), CustomHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopped Omniwheel Studio Web GUI.")


def cmd_create_urdf(args):
    """Generate URDF/Xacro from YAML configuration."""
    cfg_file = args.config_opt or args.config
    input_path = Path(cfg_file) if cfg_file else None
    if not input_path:
        if DEFAULT_CONFIG.exists():
            input_path = DEFAULT_CONFIG
        elif EXAMPLE_CONFIG.exists():
            input_path = EXAMPLE_CONFIG
        else:
            print(f"❌ Error: No configuration file found at {DEFAULT_CONFIG} or {EXAMPLE_CONFIG}")
            sys.exit(1)

    print(f"📖 Reading configuration from: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    roller_data = compute_roller_data(config)
    output_path = Path(args.output)

    if args.standalone:
        content = generate_full_standalone_urdf(config, roller_data, wheel_name=args.wheel_name)
    else:
        content = generate_urdf_snippet(config, roller_data, prefix=args.prefix)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Generated URDF ({len(roller_data)} rollers) saved to: {output_path}")


def cmd_gen_yaml(args):
    """Generate YAML configuration file."""
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.preset and args.preset in PRESETS:
        p = PRESETS[args.preset]
        print(f"⚙️ Using preset: {p['name']}")
        config = calculate_roller_positions_from_layers(
            wheel_radius=p["wheel_radius"],
            tangent_radius=p["tangent_radius"],
            roller_shape=p.get("roller_shape", "sphere"),
            roller_length=p.get("roller_length"),
            roller_weight=p["roller_weight"],
            roller_method=p["roller_method"],
            layers=p["layers"]
        )
    else:
        # Default dual-layer configuration
        layers = [
            {"offset": -0.012, "angle": 0.0, "rollers": args.rollers_per_layer},
            {"offset": 0.012, "angle": 360.0 / (args.rollers_per_layer * 2), "rollers": args.rollers_per_layer}
        ]
        config = calculate_roller_positions_from_layers(
            wheel_radius=args.wheel_radius,
            tangent_radius=args.tangent_radius,
            roller_shape=args.roller_shape,
            roller_length=args.roller_length,
            roller_weight=args.roller_weight,
            roller_method=args.roller_method,
            layers=layers
        )

    yaml_text = generate_yaml_string(config)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(yaml_text)

    print(f"✅ YAML saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Omniwheel Collision URDF Studio CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # GUI Command
    gui_parser = subparsers.add_parser("gui", help="Start Web GUI Studio")
    gui_parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    gui_parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    gui_parser.add_argument("--reload", action="store_true", help="Enable live auto-reload")

    # Create URDF Command
    urdf_parser = subparsers.add_parser("create-urdf", help="Generate collision URDF/Xacro from YAML")
    urdf_parser.add_argument("config", nargs="?", default=None, help="Input YAML file path")
    urdf_parser.add_argument("-c", "--config-file", dest="config_opt", default=None, help="Input YAML file path (alternative)")
    urdf_parser.add_argument("-o", "--output", default="output.txt", help="Output file path (default: output.txt)")
    urdf_parser.add_argument("--prefix", default="${prefix}", help="Xacro prefix parameter")
    urdf_parser.add_argument("--wheel-name", default="omni_wheel", help="Wheel link name")
    urdf_parser.add_argument("--standalone", action="store_true", help="Generate full standalone robot URDF")

    # Gen YAML Command
    yaml_parser = subparsers.add_parser("gen-yaml", help="Generate YAML wheel configuration")
    yaml_parser.add_argument("-o", "--output", default="wheel_config/omni_wheel_config.yml", help="Output YAML file path")
    yaml_parser.add_argument("--preset", choices=list(PRESETS.keys()), default=None, help="Use a built-in preset")
    yaml_parser.add_argument("--wheel-radius", type=float, default=0.06175, help="Wheel base radius (m)")
    yaml_parser.add_argument("--roller-shape", choices=["o11", "s6", "s4", "s8", "s10", "c7", "c4", "sphere", "cylinder"], default="o11", help="Collider model (Paper: o11, s6, s4, s8, s10, c7, c4; Basic: sphere, cylinder)")
    yaml_parser.add_argument("--roller-length", type=float, default=None, help="Roller length in meters (default: tangent_radius * 2.5)")
    yaml_parser.add_argument("--roller-weight", type=float, default=0.010, help="Roller mass (kg)")
    yaml_parser.add_argument("--roller-method", choices=["rotation", "axis"], default="rotation", help="Orientation method (default: rotation)")
    yaml_parser.add_argument("--rollers-per-layer", type=int, default=12, help="Number of rollers per layer")

    args = parser.parse_args()

    if args.command == "gui":
        cmd_gui(args)
    elif args.command == "create-urdf":
        cmd_create_urdf(args)
    elif args.command == "gen-yaml":
        cmd_gen_yaml(args)
    else:
        # Default behavior if no subcommand: start GUI
        parser.print_help()


if __name__ == "__main__":
    main()
