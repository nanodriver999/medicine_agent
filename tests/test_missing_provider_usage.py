from types import SimpleNamespace
from amo.agent_policy import EvaluationSession, run_strands_round
from amo.core import Budget
from amo.currency_budget import CurrencyBudget
from amo.llm_usage import LLMUsageLedger, Pricing


def session():
    return EvaluationSession({"m1": "CCO"}, lambda *_: {"status": "ok", "value": 0.2},
                             {"model": {"task"}}, {"model": 1}, Budget(2, 2))


def test_missing_provider_usage_not_successful_verification():
    budget = CurrencyBudget(1, "USD")
    ledger = LLMUsageLedger(Pricing(1, 2), "test")
    result = run_strands_round(
        session(), None, usage_ledger=ledger, currency_budget=budget,
        maximum_llm_currency_cost=0.5,
        agent_callable=lambda _: SimpleNamespace(metrics=None))
    assert result["status"] == "incomplete_usage"
    assert result["token_usage"]["status"] == "missing_provider_usage"
    assert budget.snapshot()["spent"] == 0.5
    assert ledger.summary()["usage_status"] == "missing_provider_usage"
