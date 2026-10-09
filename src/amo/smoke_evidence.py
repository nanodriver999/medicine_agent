"""Strict evidence check for a reported real-model ten-compound smoke test."""
from __future__ import annotations
import math


def validate_smoke_evidence(report: dict, *, required_count: int = 10) -> dict:
    if not isinstance(report, dict) or not isinstance(required_count, int) or required_count < 1:
        raise ValueError("invalid evidence")
    if report.get("source") != "live-admet-ai" or report.get("status") != "ok":
        raise ValueError("real inference did not finish successfully")
    calls = report.get("calls")
    if not isinstance(calls, list) or len(calls) != required_count:
        raise ValueError("incorrect number of model predictions")
    if report.get("successes") != required_count:
        raise ValueError("prediction coverage incomplete")
    endpoint = report.get("endpoint")
    if not isinstance(endpoint, dict) or not all(
        isinstance(endpoint.get(k), str) and endpoint[k]
        for k in ("name", "direction", "unit", "revision")
    ):
        raise ValueError("endpoint metadata missing")
    if endpoint["direction"] not in ("min", "max"):
        raise ValueError("invalid score direction")
    molecules = set()
    total_cost = 0.
    for call in calls:
        if not isinstance(call, dict) or call.get("status") != "ok":
            raise ValueError("failed prediction in evidence")
        smiles = call.get("smiles")
        if not isinstance(smiles, str) or not smiles or smiles in molecules:
            raise ValueError("duplicate or invalid candidate")
        molecules.add(smiles)
        if call.get("endpoint") != endpoint["name"] or call.get("model_revision") != endpoint["revision"]:
            raise ValueError("mixed endpoint or revision")
        value = call.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("nonfinite predicted score")
        cost = call.get("cost_units")
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
            raise ValueError("invalid cost")
        total_cost += cost
    return {"verified_prediction_count": len(molecules),
            "model_package_version": report.get("package_version", "unknown"),
            "reported_cost_units": total_cost,
            "scientific_validity_verified": False,
            "warning": "Execution and schema checks only; not accuracy or toxicity calibration."}
