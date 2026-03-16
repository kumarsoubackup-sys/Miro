import json
import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICES_ROOT = Path(__file__).resolve().parents[1] / "app" / "services"

app_pkg = types.ModuleType("app")
app_pkg.__path__ = []
services_pkg = types.ModuleType("app.services")
services_pkg.__path__ = [str(SERVICES_ROOT)]
sys.modules["app"] = app_pkg
sys.modules["app.services"] = services_pkg

full_name = "app.services.theme_equity_decomposer"
spec = spec_from_file_location(full_name, SERVICES_ROOT / "theme_equity_decomposer.py")
module = module_from_spec(spec)
sys.modules[full_name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


def _load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_build_theme_equity_decomposition_for_robotics_v2():
    payload = module.build_theme_equity_decomposition(
        _load_json("research/analysis/2026-03-16-robotics-actuation-source-bundle-v2.json"),
        _load_json("research/analysis/2026-03-16-robotics-actuation-structural-parse-v2.json"),
        _load_json("research/analysis/2026-03-16-robotics-actuation-graduation-v2.json"),
    )

    assert payload["decomposer_version"] == "v1"
    assert payload["theme"] == "Robotics Supply Chain"
    assert payload["row_count"] == 3
    assert payload["summary"]["top_underlyings"][0] == "MP"
    assert {row["underlying"] for row in payload["rows"]} == {"MP", "NEO", "UUUU"}

    rows = {row["underlying"]: row for row in payload["rows"]}
    assert rows["MP"]["company_role"] == "anchor"
    assert "Neodymium Processing" in rows["MP"]["linked_process_layers"]
    assert "Sintered NdFeB Magnet Manufacturing" in rows["MP"]["linked_process_layers"]

    assert rows["NEO"]["company_role"] == "satellite"
    assert rows["NEO"]["linked_process_layers"] == ["NdFeB Magnetic Powders and Alloys"]

    assert rows["UUUU"]["company_role"] == "satellite"
    assert "Neodymium Processing" in rows["UUUU"]["linked_process_layers"]
