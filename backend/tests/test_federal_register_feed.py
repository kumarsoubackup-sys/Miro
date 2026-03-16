import io
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

full_name = "app.services.federal_register_feed"
spec = spec_from_file_location(full_name, SERVICES_ROOT / "federal_register_feed.py")
module = module_from_spec(spec)
sys.modules[full_name] = module
assert spec.loader is not None
spec.loader.exec_module(module)


def _load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_build_federal_register_documents_url():
    url = module.build_federal_register_documents_url(
        query="rare earth robotics",
        agencies=["bureau-of-industry-and-security"],
        document_types=["RULE"],
        published_gte="2026-01-01",
        per_page=15,
        page=2,
    )
    assert "conditions%5Bterm%5D=rare+earth+robotics" in url
    assert "conditions%5Bagencies%5D%5B%5D=bureau-of-industry-and-security" in url
    assert "conditions%5Btype%5D%5B%5D=RULE" in url
    assert "conditions%5Bpublication_date%5D%5Bgte%5D=2026-01-01" in url
    assert "per_page=15" in url
    assert "page=2" in url


def test_fetch_federal_register_policy_feed_normalizes_results(monkeypatch):
    api_payload = _load_json("research/templates/federal-register-api-sample-response-v1.json")

    def fake_urlopen(request, timeout=20):
        return _FakeResponse(api_payload)

    monkeypatch.setattr(module, "urlopen", fake_urlopen)

    payload = module.fetch_federal_register_policy_feed(
        query="rare earth robotics",
        agencies=["bureau-of-industry-and-security"],
        target_themes=["robotics_supply_chain", "critical_materials"],
        focus_process_layers=["Neodymium Processing"],
        focus_geographies=["China"],
        ticker_refs=["MP", "UUUU"],
        policy_scope=["export_control"],
        per_page=5,
    )

    assert payload["synthetic_sample"] is False
    assert payload["fetch_metadata"]["result_count"] == 2
    assert len(payload["feed_documents"]) == 2
    first = payload["feed_documents"][0]
    assert first["source_target_id"] == "src_target_federal_register_notices"
    assert first["source_class"] == "government_policy_enforcement"
    assert "Neodymium Processing" in first["research_tags"]["process_layers"]
    assert any(
        relationship["relationship_type"] == "AFFECTED_BY_EVENT"
        for relationship in first["relationship_hints"]
    )
    assert first["ticker_refs"] == ["MP", "UUUU"]

