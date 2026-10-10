"""Auditable total-cost reconciliation.

Chemical evaluation cost units and provider currency are *not* interchangeable.
A declared conversion and compatible currency are required to report a total.
"""
from __future__ import annotations
import math


def _nonnegative(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field}: expected numeric")
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{field}: invalid amount")
    return float(value)


def reconcile_costs(*, evaluation_cost_units, llm_cost,
                    currency_per_evaluation_unit=None, currency=None):
    """Return an explicitly incomplete status unless full pricing is verifiable.

    A currency conversion is an external experimental *assumption*, never a
    property inferred from the synthetic unit ledger. A missing LLM usage
    record must not be silently converted into zero cost.
    """
    evaluation_units = _nonnegative(evaluation_cost_units, "evaluation_cost_units")
    result = {
        "evaluation_cost_units": evaluation_units,
        "llm_cost_currency": None,
        "evaluation_cost_currency": None,
        "total_cost_currency": None,
        "currency": currency,
        "status": "incomplete",
    }
    if not isinstance(llm_cost, dict) or llm_cost.get("usage_status") != "verified":
        result["reason"] = "missing_verified_llm_usage"
        return result
    if not isinstance(currency, str) or not currency.strip():
        result["reason"] = "missing_currency"
        return result
    if currency_per_evaluation_unit is None:
        result["reason"] = "missing_evaluation_unit_conversion"
        return result
    conversion = _nonnegative(currency_per_evaluation_unit, "currency_per_evaluation_unit")
    llm = _nonnegative(llm_cost.get("llm_cost_units"), "llm_cost_units")
    # The ledger has no inherent currency. The caller must explicitly attest
    # that its pricing is in the same stated currency.
    if llm_cost.get("currency") != currency:
        result["reason"] = "incompatible_llm_currency"
        return result
    result.update({
        "llm_cost_currency": llm,
        "evaluation_cost_currency": evaluation_units * conversion,
        "total_cost_currency": llm + evaluation_units * conversion,
        "status": "complete",
        "reason": None,
        "conversion_assumption": conversion,
    })
    return result
