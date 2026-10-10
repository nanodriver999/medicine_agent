"""Bounded invocation hook for provider-priced LLM calls.

Callers must obtain a defensible upper bound in the same currency before
dispatch. Provider usage is separately verified after the invocation.
"""
from __future__ import annotations
from collections.abc import Callable
from typing import Any
from .currency_budget import CurrencyBudget


def invoke_with_reservation(
    *,
    budget: CurrencyBudget,
    request_id: str,
    maximum_currency_cost: float,
    invoke: Callable[[], Any],
    actual_cost: Callable[[Any], float | None],
) -> dict:
    """Never invoke a provider without a successful advance reservation.

    Exceptions and missing usage conservatively charge the full reservation.
    The result retains the status of the original execution but does not
    disclose exception text (which may include credentials).
    """
    budget.reserve(request_id, maximum_currency_cost)
    try:
        result = invoke()
    except Exception as exc:
        billed = budget.settle(request_id, None)
        return {"status": "failed", "error_code": type(exc).__name__,
                "charged": billed, "budget": budget.snapshot()}
    try:
        measured = actual_cost(result)
        billed = budget.settle(request_id, measured)
    except Exception as exc:
        # If usage parsing or settlement fails, the reservation remains held.
        # The caller must resolve the ambiguous provider charge rather than
        # risk another unaccounted request.
        return {"status": "unreconciled", "error_code": type(exc).__name__,
                "budget": budget.snapshot()}
    return {"status": "ok", "result": result, "charged": billed,
            "budget": budget.snapshot()}
