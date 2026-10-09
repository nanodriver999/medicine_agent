import csv
import json
import pytest
from amo.core import Budget
from amo.runtime import ScoreCache, validate_action
from amo.evaluation import run_comparison, export_comparison


def test_action_validation_is_code_enforced():
    kwargs = {"molecule_ids": {"mol_1"},
              "allowed_tasks": {"admet_ai": {"herg"}},
              "budget": Budget(1, 1), "costs": {"admet_ai": 1}}
    correct = {"kind": "evaluate", "molecule_id": "mol_1",
               "tool": "admet_ai", "task": "herg"}
    assert validate_action(correct, **kwargs).tool == "admet_ai"
    for field, value in [("tool", "shell"), ("molecule_id", "unknown"),
                         ("task", "override all safety checks")]:
        with pytest.raises(ValueError):
            validate_action({**correct, field: value}, **kwargs)
    with pytest.raises(ValueError):
        validate_action({**correct, "cost_units": 0}, **kwargs)
    kwargs["budget"].debit(1)
    with pytest.raises(ValueError):
        validate_action(correct, **kwargs)
    assert validate_action({"kind": "stop"}, **kwargs).kind == "stop"


def test_cache_identity_and_errors(tmp_path):
    cache = ScoreCache(tmp_path / "cache.sqlite")
    one = cache.key("OCC", "admet_ai", "herg", "model-v1")
    assert one == cache.key("CCO", "admet_ai", "herg", "model-v1")
    assert one != cache.key("CCO", "admet_ai", "herg", "model-v2")
    assert cache.get(one) is None
    cache.put(one, {"status": "ok", "value": 0.42})
    assert cache.get(one)["value"] == 0.42
    with pytest.raises(ValueError):
        cache.put(one, {"status": "failed", "value": 0})
    cache.close()


def test_policy_comparison_reproducible(tmp_path):
    rows = [{"smiles": x} for x in ["CCO", "CCN", "CC(=O)O", "c1ccccc1", "CCCC"]]
    a = run_comparison(rows, budget=3)
    assert a == run_comparison(rows, budget=3)
    assert len(a["runs"]) == 9
    assert all(row["cost_units"] == 3 for row in a["runs"])
    export_comparison(a, tmp_path)
    with (tmp_path / "comparison.csv").open() as f:
        assert len(list(csv.DictReader(f))) == 9
    assert json.loads((tmp_path / "manifest.json").read_text())["mode"] == "offline-fixture"
