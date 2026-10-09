import pytest
from amo.core import (standardize, prepare, descriptors, similarity, diversity,
                      dominates, pareto_front, Budget, run, save_run)

POOL = [{"smiles": s} for s in ["CCO", "OCC", "CC(=O)O", "c1ccccc1", "CCN", "not_a_smiles", ""]]


def test_invalid_and_canonical_dedup():
    assert standardize("") is None
    assert standardize("not_a_smiles") is None
    assert standardize("OCC") == standardize("CCO")
    assert len(prepare(POOL)) == 4


def test_descriptors_and_diversity():
    score = descriptors("CCO")
    assert score["status"] == "ok"
    assert 0 <= score["qed"] <= 1
    assert score["mw"] > 0
    assert descriptors("not_a_smiles")["status"] == "invalid"
    assert similarity("CCO", "OCC") == 1
    assert diversity(["CCO", "OCC"]) == 0
    assert similarity("CCO", "CCN") == similarity("CCN", "CCO")


def test_pareto_directions_and_missing():
    directions = {"good": "max", "risk": "min"}
    a = {"good": 2, "risk": 1}
    b = {"good": 1, "risk": 2}
    c = {"good": 3, "risk": 3}
    unknown = {"good": 100, "risk": None}
    assert dominates(a, b, directions)
    assert not dominates(unknown, a, directions)
    assert pareto_front([a, b, c, unknown], directions) == [a, c]


def test_budget_boundaries():
    b = Budget(2, 2)
    assert b.permits(1)
    b.debit(1)
    b.debit(1)
    assert not b.permits(0)
    with pytest.raises(ValueError):
        b.debit(1)
    with pytest.raises(ValueError):
        Budget(-1, 2)


@pytest.mark.parametrize("policy", ["fixed", "rules", "agent"])
def test_offline_e2e_deterministic(tmp_path, policy):
    result = run(POOL, policy, seed=42, max_cost_units=3, max_tool_calls=3)
    other = run(POOL, policy, seed=42, max_cost_units=3, max_tool_calls=3)
    assert result == other
    assert len(result["evaluated"]) == 3
    assert result["budget"]["used_cost_units"] == 3
    assert all(r["fixture_risk_source"] == "offline-fixture" for r in result["evaluated"])
    save_run(result, tmp_path)
    assert (tmp_path / "run.json").exists()
    assert (tmp_path / "calls.jsonl").exists()
    assert (tmp_path / "pareto.csv").exists()
