import json
import pytest
from amo.checkpoint import run_resumable

POOL = [{"smiles": s} for s in ["CCO", "CCN", "CCC", "CC(=O)O", "c1ccccc1"]]


def test_resume_after_interruption_matches_fresh_run(tmp_path):
    out = tmp_path / "resumed"
    first = run_resumable(POOL, out, policy="rules", seed=42, budget_units=3,
                          max_new_calls=1)
    assert first["complete"] is False
    assert len(first["evaluated"]) == 1
    second = run_resumable(POOL, out, policy="rules", seed=42, budget_units=3)
    fresh = run_resumable(POOL, tmp_path / "fresh", policy="rules",
                          seed=42, budget_units=3)
    assert second["complete"]
    assert second["evaluated"] == fresh["evaluated"]
    assert second["calls"] == fresh["calls"]
    third = run_resumable(POOL, out, policy="rules", seed=42, budget_units=3)
    assert third["calls"] == second["calls"]
    assert json.loads((out / "manifest.json").read_text())["complete"]


def test_resume_rejects_changed_input_config(tmp_path):
    out = tmp_path / "resume"
    run_resumable(POOL, out, policy="fixed", budget_units=2, max_new_calls=1)
    with pytest.raises(ValueError):
        run_resumable(POOL, out, policy="rules", budget_units=2)
    with pytest.raises(ValueError):
        run_resumable(POOL[1:], out, policy="fixed", budget_units=2)
    with pytest.raises(ValueError):
        run_resumable(POOL, out, policy="fixed", budget_units=3)
