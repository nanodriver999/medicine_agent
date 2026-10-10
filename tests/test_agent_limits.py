import pytest
from amo.agent_policy import EvaluationSession
from amo.core import Budget

def make(*, limit=3, seconds=30, clock=lambda: 0):
    calls = []
    session = EvaluationSession(
        {"m1": "CCO", "m2": "CCN"},
        lambda *_: (calls.append(1) or {"status": "ok", "value": 0.3, "cost_units": 1}),
        {"model": {"task"}}, {"model": 1}, Budget(10, 10),
        max_actions=limit, max_wall_seconds=seconds, clock=clock)
    return session, calls

def test_invalid_proposals_count_toward_limit():
    s, calls = make(limit=2)
    assert s.evaluate("m1", "shell", "task")["status"] == "rejected"
    assert s.evaluate("m1", "shell", "task")["status"] == "rejected"
    assert s.evaluate("m1", "model", "task")["reason"] == "ActionLimit"
    assert calls == []
    assert s.budget.used_cost_units == 0

def test_deadline_before_evaluation():
    now = [0]
    s, calls = make(seconds=2, clock=lambda: now[0])
    now[0] = 2
    assert s.evaluate("m1", "model", "task")["reason"] == "WallDeadline"
    assert calls == []
    assert s.policy_state()["wall_deadline_reached"]

def test_valid_calls_within_limit():
    s, calls = make(limit=2)
    assert s.evaluate("m1", "model", "task")["status"] == "ok"
    assert s.evaluate("m2", "model", "task")["status"] == "ok"
    assert len(calls) == 2
    assert s.policy_state()["remaining_actions"] == 0

@pytest.mark.parametrize("limit,seconds", [(0,10),(1,0),(True,5),(3,float("nan"))])
def test_invalid_configuration(limit,seconds):
    with pytest.raises(ValueError):
        make(limit=limit,seconds=seconds)
