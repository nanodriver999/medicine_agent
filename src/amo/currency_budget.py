"""Single-threaded preflight reservation of comparable currency budgets.

Reservation is a policy ceiling, not proof of provider billing. No action may
start unless its maximum configured cost can be reserved. Missing bounds fail
closed; reservations must be settled even after failed calls.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field


def amount(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
        raise ValueError("cost must be a finite nonnegative amount")
    return float(v)


@dataclass
class CurrencyBudget:
    limit: float
    currency: str
    spent: float = 0
    pending: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.limit, self.spent = amount(self.limit), amount(self.spent)
        if self.spent > self.limit or not isinstance(self.currency, str) or not self.currency.strip():
            raise ValueError("invalid budget configuration")

    def reserve(self, request_id: str, maximum: float) -> None:
        maximum = amount(maximum)
        if not isinstance(request_id, str) or not request_id or request_id in self.pending:
            raise ValueError("invalid or duplicate request identifier")
        if self.spent + sum(self.pending.values()) + maximum > self.limit + 1e-12:
            raise ValueError("InsufficientReservedBudget")
        self.pending[request_id] = maximum

    def settle(self, request_id: str, observed: float | None) -> float:
        if request_id not in self.pending:
            raise ValueError("unreserved request")
        maximum = self.pending[request_id]
        # Unknown or unverified provider usage conservatively spends the
        # entire reservation. Excess usage is a contract failure, not silently
        # clipped to a cheap amount.
        if observed is not None and amount(observed) > maximum + 1e-12:
            raise ValueError("provider cost exceeded reserved ceiling")
        charged = maximum if observed is None else amount(observed)
        self.spent += charged
        del self.pending[request_id]
        return charged

    def snapshot(self) -> dict:
        return {"currency": self.currency, "limit": self.limit,
                "spent": self.spent, "reserved": sum(self.pending.values()),
                "remaining": max(0., self.limit-self.spent-sum(self.pending.values()))}
