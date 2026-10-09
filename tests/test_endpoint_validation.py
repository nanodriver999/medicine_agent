import pytest
from amo.endpoint_validation import assert_endpoint_present


def test_exact_key():
    record = {"endpoints": [{"name": "real_key", "numeric_finite": True, "sample_value": 0.2}]}
    assert_endpoint_present(record, "real_key")
    for key in ("wrong", "Real_Key", ""):
        with pytest.raises(ValueError):
            assert_endpoint_present(record, key)


def test_malformed_inventory():
    values = [{}, {"endpoints": []},
              {"endpoints": [{"name": "x", "numeric_finite": True, "sample_value": float("nan")}]},
              {"endpoints": [{"name": "x", "numeric_finite": True, "sample_value": 0.2},
                             {"name": "x", "numeric_finite": True, "sample_value": 0.2}]}]
    for item in values:
        with pytest.raises(ValueError):
            assert_endpoint_present(item, "x")
