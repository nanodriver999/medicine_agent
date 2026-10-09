import time
import pytest
from amo.isolated_worker import invoke_bounded, predict_with_deadline


def fast(smiles):
    return {"risk": 0.3}


def hang(smiles):
    time.sleep(10)
    return {"risk": 0.2}


def explode(smiles):
    raise RuntimeError("API SECRET should not escape")


def invalid(smiles):
    return {"risk": "not a value"}


def test_worker_success():
    response = invoke_bounded("CCO", timeout_seconds=5, predictor=fast)
    assert response["status"] == "ok"
    assert response["raw"]["risk"] == 0.3


def test_timeout_kills_process():
    start = time.monotonic()
    response = invoke_bounded("CCO", timeout_seconds=0.4, predictor=hang)
    assert response == {"status": "failed", "error_code": "HardTimeout", "value": None}
    assert time.monotonic() - start < 7


def test_crash_is_sanitized():
    response = invoke_bounded("CCO", timeout_seconds=5, predictor=explode)
    assert response["status"] == "failed"
    assert response["error_code"] == "RuntimeError"
    assert "SECRET" not in str(response)


def test_result_not_assumed_numeric():
    response = invoke_bounded("CCO", timeout_seconds=5, predictor=invalid)
    assert response["status"] == "ok"
    assert response["raw"]["risk"] == "not a value"


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), True])
def test_timeout_validation(timeout):
    with pytest.raises(ValueError):
        invoke_bounded("CCO", timeout_seconds=timeout, predictor=fast)
