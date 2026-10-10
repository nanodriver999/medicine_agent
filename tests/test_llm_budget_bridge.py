from amo.currency_budget import CurrencyBudget
from amo.llm_budget_bridge import invoke_with_reservation

def test_reserve_before_invoke():
    budget = CurrencyBudget(2, "USD")
    calls = []
    r = invoke_with_reservation(
        budget=budget,request_id="one",maximum_currency_cost=1,
        invoke=lambda: (calls.append(budget.snapshot()["reserved"]) or {"usage":0.2}),
        actual_cost=lambda value: value["usage"])
    assert calls == [1]
    assert r["charged"] == 0.2
    assert budget.snapshot()["reserved"] == 0

def test_reject_unauthorized_cost_without_invocation():
    budget = CurrencyBudget(1,"USD")
    called=[]
    try:
        invoke_with_reservation(budget=budget,request_id="x",maximum_currency_cost=2,
                                invoke=lambda: called.append(1),actual_cost=lambda _:0)
        assert False
    except ValueError:
        pass
    assert called == []

def test_failed_call_reserves_worst_case():
    b=CurrencyBudget(1,"USD")
    def broken():
        raise TimeoutError("secret")
    result=invoke_with_reservation(budget=b,request_id="failed",
        maximum_currency_cost=1,invoke=broken,actual_cost=lambda _:0)
    assert result["status"]=="failed"
    assert result["charged"]==1
    assert "secret" not in str(result)

def test_unknown_provider_usage_charges_maximum():
    b=CurrencyBudget(1,"USD")
    r=invoke_with_reservation(budget=b,request_id="missing",
        maximum_currency_cost=1,invoke=lambda: {"ok":True},actual_cost=lambda _:None)
    assert r["charged"]==1

def test_over_ceiling_usage_blocks_further_dispatch():
    b=CurrencyBudget(2,"USD")
    result=invoke_with_reservation(budget=b,request_id="over",
        maximum_currency_cost=1,invoke=lambda: {"charged":3},
        actual_cost=lambda data:data["charged"])
    assert result["status"]=="unreconciled"
    assert b.snapshot()["reserved"]==1
