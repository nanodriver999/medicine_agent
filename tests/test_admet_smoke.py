from amo.admet_smoke import run_smoke, export_smoke
from amo.admet import ADMETAdapter, Endpoint
import json
import pytest


def test_contract_smoke_and_logging(tmp_path):
    endpoint = Endpoint("example_task", "min", "model_native", "fake-v1")
    adapter = ADMETAdapter(endpoint,
        predictor=lambda smiles: {"example_task": len(smiles) / 100})
    report = run_smoke([{"smiles": x} for x in ["CCO", "CCN", "CCC"]],
                       endpoint, max_count=3, adapter=adapter)
    assert report["status"] == "ok"
    assert report["successes"] == 3
    assert report["budget"]["used_cost_units"] == 3
    assert report["source"] == "injected-test-predictor"
    export_smoke(report, tmp_path)
    assert len((tmp_path / "calls.jsonl").read_text().splitlines()) == 3
    assert json.loads((tmp_path / "admet_smoke.json").read_text())["successes"] == 3


def test_errors_are_not_imputed():
    endpoint = Endpoint("task", "min", "unit", "v1")
    adapter = ADMETAdapter(endpoint, predictor=lambda smiles: {})
    report = run_smoke([{"smiles": "CCO"}], endpoint, max_count=1, adapter=adapter)
    assert report["status"] == "partial_failure"
    assert report["calls"][0]["value"] is None
    assert report["budget"]["used_cost_units"] == 1


def test_requires_requested_valid_count():
    endpoint = Endpoint("task", "min", "unit", "v1")
    with pytest.raises(ValueError):
        run_smoke([{"smiles": "CCO"}, {"smiles": "OCC"}], endpoint, max_count=2,
                  adapter=ADMETAdapter(endpoint, predictor=lambda _: {"task": 0.5}))
