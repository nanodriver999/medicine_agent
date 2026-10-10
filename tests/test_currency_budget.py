import pytest
from amo.currency_budget import CurrencyBudget


def test_reserve_settle_and_reuse():
    b=CurrencyBudget(10,"USD")
    b.reserve("llm-1", 7)
    with pytest.raises(ValueError):
        b.reserve("admet-1",4)
    assert b.settle("llm-1",3)==3
    b.reserve("admet-1",4)
    assert b.settle("admet-1",2)==2
    assert b.snapshot()["remaining"]==5


def test_unverified_cost_charges_reserved_worst_case():
    b=CurrencyBudget(5,"USD")
    b.reserve("llm-1",5)
    assert b.settle("llm-1",None)==5
    with pytest.raises(ValueError):
        b.reserve("next",0.01)


def test_overspend_and_bad_values_fail():
    b=CurrencyBudget(3,"USD")
    b.reserve("request",2)
    with pytest.raises(ValueError):
        b.settle("request",3)
    assert b.snapshot()["reserved"]==2
    for v in (-1,float("nan"),True):
        with pytest.raises(ValueError):
            b.reserve("bad",v)
    with pytest.raises(ValueError):
        b.reserve("request",0)


def test_unreserved_settlement_rejected():
    with pytest.raises(ValueError):
        CurrencyBudget(1,"USD").settle("unknown",0)
