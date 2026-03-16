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


def _load_module(name: str):
    services_root = Path(__file__).resolve().parents[1] / "backend" / "app" / "services"

    app_pkg = types.ModuleType("app")
    app_pkg.__path__ = []
    services_pkg = types.ModuleType("app.services")
    services_pkg.__path__ = [str(services_root)]
    sys.modules.setdefault("app", app_pkg)
    sys.modules.setdefault("app.services", services_pkg)

    full_name = f"app.services.{name}"
    if full_name not in sys.modules:
        spec = spec_from_file_location(full_name, services_root / f"{name}.py")
        module = module_from_spec(spec)
        sys.modules[full_name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)

    return sys.modules[full_name]


def main() -> int:
    # Load profiles module first so we can list available names in help text.
    profiles_module = _load_module("federal_register_query_profiles")
    available_profiles = profiles_module.list_query_profiles()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--query-profile",
        choices=available_profiles,
        help=f"Use a curated query profile. Available: {', '.join(available_profiles)}",
    )
    parser.add_argument("--list-profiles", action="store_true", help="List available profiles and exit")
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
    parser.add_argument("--output-json", type=Path)
    args = parser.parse_args()

    if args.list_profiles:
        for name in available_profiles:
            profile = profiles_module.get_query_profile(name)
            print(f"  {name}: query={profile.get('query', '')!r}")
        return 0

    if not args.output_json:
        parser.error("--output-json is required (unless --list-profiles is used)")

    feed_module = _load_module("federal_register_feed")
    payload = feed_module.fetch_federal_register_policy_feed(
        query_profile=args.query_profile,
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
