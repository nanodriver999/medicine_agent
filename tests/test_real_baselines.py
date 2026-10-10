import pytest
from amo.admet import ADMETAdapter, Endpoint
from amo.real_baselines import run_baseline

POOL = [{"molecule_id": f"m{i}", "smiles": s}
        for i, s in enumerate(["CCO", "CCN", "CCC", "CCCC", "CC(=O)O"])]

@pytest.mark.parametrize("policy", ["fixed", "rules"])
def test_baseline_budget(policy):
    ep = Endpoint("risk", "min", "model-native", "fake-v1")
    model = ADMETAdapter(ep, predictor=lambda s: {"risk": len(s) / 100})
    result = run_baseline(POOL, ep, policy, 3, adapter=model)
    assert len(result["evaluated"]) == 3
    assert result["budget"]["used_cost_units"] == 3
    assert result["source"] == "injected-adapter"

def test_failed_score_does_not_enter_pareto():
    ep = Endpoint("risk", "min", "native", "fake-v1")
    model = ADMETAdapter(ep, predictor=lambda s: {})
    result = run_baseline(POOL, ep, "fixed", 2, adapter=model)
    assert result["evaluated"] == []
    assert result["pareto"] == []
    assert result["budget"]["used_cost_units"] == 2

def test_invalid_policy_and_budget():
    ep = Endpoint("risk", "min", "native", "fake-v1")
    model = ADMETAdapter(ep, predictor=lambda s: {"risk": 0.2})
    with pytest.raises(ValueError):
        run_baseline(POOL, ep, "agent", 2, adapter=model)
    with pytest.raises(ValueError):
        run_baseline(POOL, ep, "fixed", -1, adapter=model)
