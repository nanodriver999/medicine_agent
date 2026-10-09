import pytest
from amo.core import descriptors
from amo.objectives import Bound, check_constraints, covered_frontier, greedy_diverse_top_k


def test_sa_score_and_limits():
    for smi in ["CCO", "CC(=O)O", "c1ccccc1"]:
        measured = descriptors(smi)
        assert measured["status"] == "ok"
        assert 1 <= measured["sa"] <= 10
        assert measured["qed"] >= 0


def test_constraints_missing_is_not_safe():
    assert not check_constraints({"qed": 0.8})["passes"]
    assert check_constraints({"qed": None}, {"qed": Bound(minimum=0.4)})["unknown"] == ["qed"]
    assert check_constraints({"qed": 0.8}, {"qed": Bound(minimum=0.4)})["passes"]
    assert not check_constraints({"qed": 0.2}, {"qed": Bound(minimum=0.4)})["passes"]


def test_coverage_safe_pareto_and_diversity():
    molecules = [dict(molecule_id=f"m{i}", **descriptors(smi))
                 for i, smi in enumerate(["CCO", "CCN", "CCCC"])]
    all_ok = {"qed": Bound(minimum=0)}
    front = covered_frontier(molecules, objectives={"qed": "max", "sa": "min"},
                             bounds=all_ok)
    assert front
    assert all("sa" in x for x in front)
    picked = greedy_diverse_top_k(molecules, 2)
    assert len(picked) == 2
    assert picked[0]["smiles"] != picked[1]["smiles"]
    with pytest.raises(ValueError):
        greedy_diverse_top_k(molecules, -1)
