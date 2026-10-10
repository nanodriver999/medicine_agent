import pytest
from amo.comparison_integrity import fingerprint_pool, verify_comparison

def runs():
    return [{"policy": name, "seed": 42, "pool_sha256": "abc",
             "model_revision": "v1", "endpoint": "risk", "budget_units": 10,
             "cache_protocol": "cold-isolated", "evaluation_cost_units": 4,
             "llm_cost_units": 0} for name in ("fixed", "rules", "agent")]

def test_equal_runs_and_total_cost():
    assert verify_comparison(runs())["status"] == "comparable"

def test_llm_cost_missing_blocks_fairness_claim():
    example = runs()
    del example[2]["llm_cost_units"]
    result = verify_comparison(example)
    assert result["conditions_match"]
    assert not result["total_cost_comparable"]

@pytest.mark.parametrize("field,value", [
    ("seed",43), ("pool_sha256","different"), ("model_revision","v2"),
    ("endpoint","other"), ("budget_units",12), ("cache_protocol","warm"),
    ("evaluation_cost_units",20),
])
def test_mismatch_or_overspend_rejected(field,value):
    example = runs()
    example[2][field] = value
    with pytest.raises(ValueError):
        verify_comparison(example)

def test_pool_fingerprint_is_order_invariant():
    a=[{"molecule_id":"a","smiles":"CCO"},{"molecule_id":"b","smiles":"CCN"}]
    assert fingerprint_pool(a) == fingerprint_pool(list(reversed(a)))
