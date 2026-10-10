import pytest
from amo.total_cost import reconcile_costs


def test_total_cost_with_explicit_identical_currency():
    result = reconcile_costs(
        evaluation_cost_units=3,
        llm_cost={"usage_status": "verified", "llm_cost_units": 0.5,
                  "currency": "USD"},
        currency_per_evaluation_unit=0.2, currency="USD")
    assert result["status"] == "complete"
    assert result["total_cost_currency"] == pytest.approx(1.1)


def test_missing_usage_and_conversion_are_incomplete_not_zero():
    result = reconcile_costs(evaluation_cost_units=1, llm_cost={},
                             currency_per_evaluation_unit=1, currency="USD")
    assert result["status"] == "incomplete"
    assert result["total_cost_currency"] is None
    assert reconcile_costs(evaluation_cost_units=1,
        llm_cost={"usage_status":"verified","llm_cost_units": 1,"currency":"USD"},
        currency="USD")["reason"] == "missing_evaluation_unit_conversion"


def test_currency_mismatch():
    result = reconcile_costs(evaluation_cost_units=1,
        llm_cost={"usage_status":"verified","llm_cost_units": 1,"currency":"EUR"},
        currency_per_evaluation_unit=1, currency="USD")
    assert result["reason"] == "incompatible_llm_currency"


@pytest.mark.parametrize("invalid", [-1,float("nan"),float("inf"),True,"zero"])
def test_invalid_costs_never_pass(invalid):
    with pytest.raises(ValueError):
        reconcile_costs(evaluation_cost_units=invalid, llm_cost={})


def test_missing_verified_llm_ledger():
    assert reconcile_costs(evaluation_cost_units=0,
         llm_cost={"usage_status": "missing_provider_usage"},
         currency_per_evaluation_unit=0, currency="USD")["status"] == "incomplete"
