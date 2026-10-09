import pytest
from amo.admet import Endpoint, ADMETAdapter
from amo.admet_smoke import run_smoke


def test_injected_adapter_never_claims_live_weights():
    endpoint = Endpoint("test", "min", "test_unit", "fake-rev")
    adapter = ADMETAdapter(endpoint, predictor=lambda _: {"test": 0.3})
    report = run_smoke([{"smiles":"CCO"}], endpoint, max_count=1, adapter=adapter)
    assert report["source"] == "injected-adapter"
    assert report["successes"] == 1


def test_invalid_response_propagates_partial_failure():
    endpoint = Endpoint("test", "min", "test_unit", "fake-rev")
    adapter = ADMETAdapter(endpoint, predictor=lambda _: {"test": "low risk"})
    report = run_smoke([{"smiles":"CCO"}], endpoint, max_count=1, adapter=adapter)
    assert report["status"] == "partial_failure"
    assert report["calls"][0]["value"] is None
