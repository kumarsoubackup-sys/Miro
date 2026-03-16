#!/usr/bin/env python3
"""
Generate a theme-to-equity decomposition artifact from a promoted structural parse.
"""

from __future__ import annotations

import argparse
import json
import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_decomposer_module():
    services_root = Path(__file__).resolve().parents[1] / "backend" / "app" / "services"

    app_pkg = types.ModuleType("app")
    app_pkg.__path__ = []
    services_pkg = types.ModuleType("app.services")
    services_pkg.__path__ = [str(services_root)]
    sys.modules["app"] = app_pkg
    sys.modules["app.services"] = services_pkg

    full_name = "app.services.theme_equity_decomposer"
    if full_name not in sys.modules:
        spec = spec_from_file_location(full_name, services_root / "theme_equity_decomposer.py")
        module = module_from_spec(spec)
        sys.modules[full_name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)

    return sys.modules[full_name]


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_bundle_json", type=Path)
    parser.add_argument("structural_parse_json", type=Path)
    parser.add_argument("graduation_json", type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()

    module = _load_decomposer_module()
    payload = module.build_theme_equity_decomposition(
        _load_json(args.source_bundle_json),
        _load_json(args.structural_parse_json),
        _load_json(args.graduation_json),
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

