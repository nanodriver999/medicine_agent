import pytest
from amo.admet import ADMETAdapter, Endpoint
from amo.runtime import ScoreCache


def endpoint():
    return Endpoint("endpoint", "min", "model-native", "test-revision", cost_units=2)


def test_transient_error_retried_and_attempts_billed(tmp_path):
    attempts = []
    sleeps = []
    def predictor(smiles):
        attempts.append(smiles)
        if len(attempts) < 3:
            raise TimeoutError("temporary network")
        return {"endpoint": 0.25}
    with_cache = ScoreCache(tmp_path / "scores.db")
    adapter = ADMETAdapter(endpoint(), predictor=predictor, cache=with_cache,
                           max_attempts=3, retry_delay_seconds=0.01, sleep=sleeps.append)
    result = adapter.evaluate("CCO")
    assert result["status"] == "ok"
    assert result["attempts"] == 3
    assert result["cost_units"] == 6
    assert sleeps == [0.01, 0.01]
    cached = adapter.evaluate("OCC")
    assert cached["cache_hit"] is True
    assert cached["cost_units"] == 0
    assert len(attempts) == 3
    with_cache.close()


def test_schema_errors_do_not_retry_or_fabricate():
    attempts = []
    def invalid(smiles):
        attempts.append(smiles)
        return {"endpoint": "safe"}
    adapter = ADMETAdapter(endpoint(), predictor=invalid, max_attempts=5)
    result = adapter.evaluate("CCO")
    assert result["status"] == "failed"
    assert result["value"] is None
    assert result["error_code"] == "ValueError"
    assert result["attempts"] == 1
    assert len(attempts) == 1


def test_bounded_failure_after_transient_errors():
    counter = []
    def flaky(_):
        counter.append(1)
        raise ConnectionError("secret data")
    adapter = ADMETAdapter(endpoint(), predictor=flaky, max_attempts=2, sleep=lambda _: None)
    result = adapter.evaluate("CCO")
    assert result["status"] == "failed"
    assert result["attempts"] == 2
    assert result["cost_units"] == 4
    assert "secret" not in str(result)
    assert len(counter) == 2


@pytest.mark.parametrize("max_attempts", [0, -1, 6, 1.5, True])
def test_bad_limits_rejected(max_attempts):
    with pytest.raises(ValueError):
        ADMETAdapter(endpoint(), predictor=lambda s: {}, max_attempts=max_attempts)
