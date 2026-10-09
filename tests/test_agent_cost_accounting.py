from amo.agent_policy import EvaluationSession
from amo.core import Budget


def _session(responses, *, budget=2, calls=3):
    iterator = iter(responses)
    return EvaluationSession(
        {"one": "CCO", "two": "CCN", "three": "CCC"},
        lambda *_: next(iterator),
        {"admet_ai": {"risk"}}, {"admet_ai": 1.0}, Budget(budget, calls))


def test_verified_cache_hit_charges_zero_but_consumes_tool_call():
    s = _session([{"status": "ok", "value": 0.4, "cost_units": 0, "cache_hit": True},
                  {"status": "ok", "value": 0.5, "cost_units": 1, "cache_hit": False}])
    a = s.evaluate("one", "admet_ai", "risk")
    b = s.evaluate("two", "admet_ai", "risk")
    assert a["cache_hit"] is True
    assert b["cache_hit"] is False
    assert s.budget.used_cost_units == 1
    assert s.budget.tool_calls == 2
    assert [e["cost_units"] for e in s.events] == [0, 1]


def test_unverified_free_cost_claim_is_charged():
    s = _session([{"status": "ok", "value": 0.4, "cost_units": 0,
                   "cache_hit": False}])
    out = s.evaluate("one", "admet_ai", "risk")
    assert out["status"] == "ok"
    assert s.budget.used_cost_units == 1
    assert s.events[0]["cost_units"] == 1


def test_malformed_or_failed_predictions_charge_conservative_cost():
    s = _session([{"status": "failed", "value": None, "cache_hit": False},
                  {"status": "ok", "value": float("nan"), "cost_units": 0,
                   "cache_hit": True}])
    assert s.evaluate("one", "admet_ai", "risk")["status"] == "failed"
    assert s.evaluate("two", "admet_ai", "risk")["status"] == "failed"
    assert s.budget.used_cost_units == 2
    assert s.budget.tool_calls == 2
    assert s.evaluate("three", "admet_ai", "risk")["status"] == "rejected"


def test_duplicate_does_not_bypass_call_limit():
    s = _session([{"status": "ok", "value": 0.5, "cache_hit": True, "cost_units": 0}])
    assert s.evaluate("one", "admet_ai", "risk")["status"] == "ok"
    assert s.evaluate("one", "admet_ai", "risk")["status"] == "rejected"
    assert s.budget.tool_calls == 1
