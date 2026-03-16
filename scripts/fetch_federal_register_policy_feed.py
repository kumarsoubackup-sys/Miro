#!/usr/bin/env python3
"""
Fetch live Federal Register documents and normalize them into policy-feed JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    services_root = Path(__file__).resolve().parents[1] / "backend" / "app" / "services"

    app_pkg = types.ModuleType("app")
    app_pkg.__path__ = []
    services_pkg = types.ModuleType("app.services")
    services_pkg.__path__ = [str(services_root)]
    sys.modules["app"] = app_pkg
    sys.modules["app.services"] = services_pkg

    full_name = "app.services.federal_register_feed"
    if full_name not in sys.modules:
        spec = spec_from_file_location(full_name, services_root / "federal_register_feed.py")
        module = module_from_spec(spec)
        sys.modules[full_name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)

    return sys.modules[full_name]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="")
    parser.add_argument("--agency", action="append", dest="agencies")
    parser.add_argument("--document-type", action="append", dest="document_types")
    parser.add_argument("--published-gte")
    parser.add_argument("--published-lte")
    parser.add_argument("--target-theme", action="append", dest="target_themes")
    parser.add_argument("--focus-process-layer", action="append", dest="focus_process_layers")
    parser.add_argument("--focus-geography", action="append", dest="focus_geographies")
    parser.add_argument("--ticker", action="append", dest="ticker_refs")
    parser.add_argument("--policy-scope", action="append", dest="policy_scope")
    parser.add_argument("--per-page", type=int, default=20)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--output-json", required=True, type=Path)
    args = parser.parse_args()

    module = _load_module()
    payload = module.fetch_federal_register_policy_feed(
        query=args.query,
        agencies=args.agencies,
        document_types=args.document_types,
        published_gte=args.published_gte,
        published_lte=args.published_lte,
        per_page=args.per_page,
        page=args.page,
        target_themes=args.target_themes,
        focus_process_layers=args.focus_process_layers,
        focus_geographies=args.focus_geographies,
        ticker_refs=args.ticker_refs,
        policy_scope=args.policy_scope,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

