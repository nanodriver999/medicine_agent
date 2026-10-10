from types import SimpleNamespace
from amo.agent_policy import EvaluationSession, run_strands_round
from amo.core import Budget
from amo.currency_budget import CurrencyBudget
from amo.llm_usage import LLMUsageLedger, Pricing


def session():
    return EvaluationSession({"m1": "CCO"}, lambda *_: {"status":"ok","value":0.2},
                             {"model":{"task"}}, {"model":1}, Budget(2,2))


def response(i=100, o=50):
    return SimpleNamespace(metrics=SimpleNamespace(
        accumulated_usage={"inputTokens":i,"outputTokens":o,"totalTokens":i+o}))


def test_real_path_receives_ledger_and_settles():
    ledger=LLMUsageLedger(Pricing(1,2),"test")
    budget=CurrencyBudget(0.001,"USD")
    result=run_strands_round(session(), None, usage_ledger=ledger,
        currency_budget=budget, maximum_llm_currency_cost=0.0005,
        agent_callable=lambda _: response())
    assert result["status"]=="ok"
    assert result["llm_cost"]["usage_status"]=="verified"
    assert budget.snapshot()["spent"]==0.0002
    assert budget.snapshot()["reserved"]==0


def test_missing_bound_rejects_before_invocation():
    called=[]
    result=run_strands_round(session(),None, currency_budget=CurrencyBudget(1,"USD"),
        agent_callable=lambda _: called.append(1))
    assert result["status"]=="rejected"
    assert called==[]


def test_provider_error_consumes_reservation():
    ledger=LLMUsageLedger(Pricing(1,2),"test")
    budget=CurrencyBudget(1,"USD")
    def broken(_):
        raise TimeoutError("sensitive")
    result=run_strands_round(session(),None,usage_ledger=ledger,
        currency_budget=budget,maximum_llm_currency_cost=0.5,agent_callable=broken)
    assert result["status"]=="failed"
    assert budget.snapshot()["spent"]==0.5
    assert "sensitive" not in str(result)


def test_excess_provider_usage_is_unreconciled():
    ledger=LLMUsageLedger(Pricing(100,100),"test")
    budget=CurrencyBudget(1,"USD")
    result=run_strands_round(session(),None,usage_ledger=ledger,
        currency_budget=budget,maximum_llm_currency_cost=0.00001,
        agent_callable=lambda _: response())
    assert result["status"]=="unreconciled"
    assert budget.snapshot()["reserved"]==0.00001
