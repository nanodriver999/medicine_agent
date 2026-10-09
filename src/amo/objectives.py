"""Preset molecular property constraints and coverage-safe ranking.

All thresholds below are research hypotheses, NOT validated drug-likeness safety gates.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Any

from .core import pareto_front, diversity


@dataclass(frozen=True)
class Bound:
    minimum: float | None = None
    maximum: float | None = None

    def check(self, value: Any) -> bool | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return None
        return ((self.minimum is None or value >= self.minimum) and
                (self.maximum is None or value <= self.maximum))


DEFAULT_PROPERTY_BOUNDS = {
    "mw": Bound(maximum=500),
    "clogp": Bound(maximum=5),
    "tpsa": Bound(maximum=140),
    "qed": Bound(minimum=0.1),
    "sa": Bound(maximum=7),
}


def check_constraints(row: dict, bounds: dict[str, Bound] | None = None) -> dict:
    """Unmeasured/invalid is unknown, never automatically passed."""
    bounds = DEFAULT_PROPERTY_BOUNDS if bounds is None else bounds
    checks = {name: bound.check(row.get(name)) for name, bound in bounds.items()}
    passed = (all(result is True for result in checks.values())
              if checks else True)
    return {"passes": passed, "checks": checks,
            "unknown": [key for key, value in checks.items() if value is None],
            "violations": [key for key, value in checks.items() if value is False]}


def covered_frontier(rows: list[dict], *, objectives: dict[str, str],
                     bounds: dict[str, Bound] | None = None) -> list[dict]:
    """A molecule must pass every explicitly required constraint and objective."""
    qualified = [row for row in rows if check_constraints(row, bounds)["passes"]]
    return pareto_front(qualified, objectives)


def greedy_diverse_top_k(frontier: list[dict], k: int) -> list[dict]:
    """Simple structural-diversity-first down-selection; no fabricated scores."""
    from .core import similarity
    if k < 0:
        raise ValueError("negative k")
    pool = sorted(frontier, key=lambda r: (r.get("molecule_id", ""), r["smiles"]))
    selected = []
    while pool and len(selected) < k:
        if not selected:
            choice = pool[0]
        else:
            choice = max(pool, key=lambda row: (
                min(1 - similarity(row["smiles"], s["smiles"]) for s in selected),
                -pool.index(row)))
        selected.append(choice)
        pool.remove(choice)
    return selected
