from amo.admet import ADMETAdapter, Endpoint
from amo.runtime import ScoreCache
import pytest


def test_model_contract_and_cache(tmp_path):
    calls = []
    def fake(smiles):
        calls.append(smiles)
        return {"hERG": 0.7}
    endpoint = Endpoint("hERG", "min", "model_native", "fixture-model-v1")
    cache = ScoreCache(tmp_path / "predictions.sqlite")
    adapter = ADMETAdapter(endpoint, predictor=fake, cache=cache)
    first = adapter.evaluate("OCC")
    second = adapter.evaluate("CCO")
    assert first["status"] == second["status"] == "ok"
    assert first["source"] == "admet_ai"
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["cost_units"] == 0
    assert first["cost_units"] == 1
    assert len(calls) == 1
    cache.close()


@pytest.mark.parametrize("prediction", [{}, {"hERG": None}, {"hERG": float("nan")},
                                       {"hERG": "low-risk"}, {"hERG": True}])
def test_model_response_invalid(prediction):
    adapter = ADMETAdapter(Endpoint("hERG", "min", "model_native", "fake-v1"),
                           predictor=lambda s: prediction)
    result = adapter.evaluate("CCO")
    assert result["status"] == "failed"
    assert result["value"] is None
    assert result["error_code"] == "ValueError"


def test_model_exception_and_invalid_input():
    def broken(s):
        raise TimeoutError("contains credentials: DO NOT LOG")
    adapter = ADMETAdapter(Endpoint("endpoint", "min", "unit", "rev"),
                           predictor=broken)
    assert adapter.evaluate("CCO")["error_code"] == "TimeoutError"
    assert adapter.evaluate("not_a_smiles")["status"] == "invalid"


def test_endpoint_rejects_missing_semantics():
    with pytest.raises(ValueError):
        Endpoint("hERG", "unknown", "unit", "rev")
    with pytest.raises(ValueError):
        Endpoint("hERG", "min", "", "rev")
