"""Explicit opt-in live model smoke test and measured execution ledger."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path

from .admet import ADMETAdapter, Endpoint
from .core import Budget, prepare
from .runtime import ScoreCache


def run_smoke(rows: list[dict], endpoint: Endpoint, *, max_count: int = 10,
              adapter: ADMETAdapter | None = None) -> dict:
    if max_count < 1:
        raise ValueError("max_count must be positive")
    candidates = prepare(rows)[:max_count]
    if len(candidates) < max_count:
        raise ValueError(f"Insufficient unique valid candidates: {len(candidates)} of {max_count}")
    injected_adapter = adapter is not None
    if adapter is None:
        adapter = ADMETAdapter(endpoint)
    maximum_per_call = endpoint.cost_units * adapter.max_attempts
    budget = Budget(maximum_per_call * max_count, max_count)
    calls = []
    for molecule in candidates:
        # For a first-time smoke each request is charged the configured cost.
        # The adapter reports cache hits as zero-cost for later reuse.
        if not budget.permits(maximum_per_call):
            break
        try:
            result = adapter.evaluate(molecule["smiles"])
        except Exception as exc:
            result = {"status": "failed", "value": None, "error_code": type(exc).__name__}
        import math
        if not isinstance(result, dict):
            result = {"status": "failed", "value": None, "error_code": "MalformedAdapterResponse"}
        claimed = result.get("cost_units")
        valid_cost = (
            isinstance(claimed, (int, float)) and not isinstance(claimed, bool)
            and math.isfinite(claimed) and 0 <= claimed <= maximum_per_call
        )
        # Unverifiable usage must not be interpreted as free inference.
        billed = float(claimed) if valid_cost else maximum_per_call
        if not budget.permits(billed):
            raise ValueError("reserved smoke budget unexpectedly exceeded")
        budget.debit(billed)
        if not valid_cost:
            result = {"status": "failed", "value": None,
                      "error_code": result.get("error_code", "UnverifiedCost")
                                    if result.get("status") != "ok" else "UnverifiedCost",
                      "cache_hit": False}
        if result.get("status") != "ok":
            result = {**result, "status": "failed", "value": None}
        calls.append({"molecule_id": molecule["molecule_id"], "smiles": molecule["smiles"],
                      "task": endpoint.name, **result, "cost_units": billed})
    successes = sum(item["status"] == "ok" for item in calls)
    execution_type = "injected-adapter" if injected_adapter else "live-admet-ai"
    try:
        installed = importlib.metadata.version("admet-ai")
    except importlib.metadata.PackageNotFoundError:
        installed = "not-installed-or-injected"
    return {
        "status": "ok" if successes == len(candidates) else "partial_failure",
        "source": execution_type,
        "endpoint": endpoint.__dict__,
        "package_version": installed,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "successes": successes,
        "calls": calls,
        "budget": budget.__dict__,
        "maximum_reserved_cost_per_call": maximum_per_call,
        "warning": "Model outputs are predictions, not experimental measurements or safety guarantees.",
    }


def export_smoke(report: dict, out: str | Path) -> None:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "admet_smoke.json").write_text(json.dumps(report, indent=2, allow_nan=False),
                                          encoding="utf-8")
    with (out / "calls.jsonl").open("w", encoding="utf-8") as fp:
        for call in report["calls"]:
            fp.write(json.dumps(call, allow_nan=False) + "\n")
