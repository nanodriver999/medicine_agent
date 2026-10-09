import pytest
from amo.agent_policy import EvaluationSession
from amo.agent_live import live_agent_run
from amo.admet import ADMETAdapter, Endpoint
from amo.core import Budget


def session(response, maximum=6, balance=6):
    return EvaluationSession({"a": "CCO", "b": "CCN"}, lambda *_: response,
                             {"admet_ai": {"task"}}, {"admet_ai": maximum},
                             Budget(balance, 2))


def test_successful_retry_charges_observed_attempts():
    instance = session({"status": "ok", "value": 0.4, "cost_units": 4,
                        "cache_hit": False})
    out = instance.evaluate("a", "admet_ai", "task")
    assert out["status"] == "ok"
    assert instance.budget.used_cost_units == 4
    assert instance.budget.tool_calls == 1


def test_failure_attempts_charge_reported_cost():
    instance = session({"status": "failed", "error_code": "TimeoutError",
                        "cost_units": 2})
    assert instance.evaluate("a", "admet_ai", "task")["status"] == "failed"
    assert instance.budget.used_cost_units == 2


def test_excessive_or_invalid_claim_never_exceeds_reservation():
    for val in [7, float("nan"), "free", -1, True]:
        instance = session({"status": "ok", "value": 0.2, "cost_units": val})
        instance.evaluate("a", "admet_ai", "task")
        assert instance.budget.used_cost_units == 6


def test_insufficient_budget_rejects_before_predicting():
    calls = []
    instance = EvaluationSession({"a": "CCO"}, lambda *_: calls.append(1),
                                 {"admet_ai": {"task"}}, {"admet_ai": 6},
                                 Budget(5, 1))
    assert instance.evaluate("a", "admet_ai", "task")["status"] == "rejected"
    assert calls == []


def test_live_session_retry_reservation_prevents_overspend():
    endpoint = Endpoint("task", "min", "unit", "v1", cost_units=2)
    attempts = []
    def predictor(smiles):
        attempts.append(smiles)
        if len(attempts) == 1:
            raise TimeoutError("temporary")
        return {"task": 0.2}
    adapter = ADMETAdapter(endpoint, predictor=predictor,
                           max_attempts=3, sleep=lambda _: None)
    def driver(session):
        molecule_id = next(iter(session.molecules))
        response = session.evaluate(molecule_id, "admet_ai", "task")
        assert response["status"] == "ok"
        return {"status": "ok"}
    result = live_agent_run([{"molecule_id": "a", "smiles": "CCO"}], endpoint,
                            budget_units=3, adapter=adapter, driver=driver)
    assert result["budget"]["used_cost_units"] == 4
    assert result["budget"]["max_cost_units"] == 6
    assert len(attempts) == 2
