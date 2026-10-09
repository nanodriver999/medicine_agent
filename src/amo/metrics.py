"""Auditable multiobjective metrics using only fully observed predictions.

2D hypervolume is defined for max QED in [0,1] and min risk in [0,1];
its reference point is fixed a priori at (QED=0, risk=1).
"""
from __future__ import annotations
import math
from .core import diversity


def hypervolume_qed_risk(rows: list[dict]) -> float:
    points = []
    for row in rows:
        qed = row.get("qed")
        risk = row.get("fixture_risk")
        if isinstance(qed, bool) or isinstance(risk, bool):
            continue
        if not isinstance(qed, (int, float)) or not isinstance(risk, (int, float)):
            continue
        if not all(math.isfinite(v) for v in (qed, risk)):
            continue
        if not (0 <= qed <= 1 and 0 <= risk <= 1):
            raise ValueError("hypervolume requires 0..1 normalized objectives")
        points.append((qed, 1 - risk))
    points.sort()
    last_x, area = 0., 0.
    for index, (qed, _) in enumerate(points):
        if qed > last_x:
            area += (qed - last_x) * max(p[1] for p in points[index:])
            last_x = qed
    return area


def cost_curve(evaluated: list[dict], cost_per_call: float = 1) -> list[dict]:
    """Budget/quality trace; never infers an unobserved endpoint."""
    if not math.isfinite(cost_per_call) or cost_per_call < 0:
        raise ValueError("invalid call cost")
    history, observed = [], []
    for item in evaluated:
        observed.append(item)
        good = [r["qed"] - r["fixture_risk"] for r in observed
                if isinstance(r.get("qed"), (int, float))
                and isinstance(r.get("fixture_risk"), (int, float))]
        history.append({"evaluations": len(observed),
                        "cost_units": len(observed) * cost_per_call,
                        "best_fixture_objective": max(good) if good else None,
                        "hypervolume_qed_risk": hypervolume_qed_risk(observed)})
    return history
