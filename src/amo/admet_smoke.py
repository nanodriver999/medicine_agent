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
    if adapter is None:
        adapter = ADMETAdapter(endpoint)
    budget = Budget(endpoint.cost_units * max_count, max_count)
    calls = []
    for molecule in candidates:
        # For a first-time smoke each request is charged the configured cost.
        # The adapter reports cache hits as zero-cost for later reuse.
        if not budget.permits(endpoint.cost_units):
            break
        result = adapter.evaluate(molecule["smiles"])
        actual_cost = float(result["cost_units"])
        if not budget.permits(actual_cost):
            raise ValueError("model reported unexpected evaluation cost")
        budget.debit(actual_cost)
        calls.append({"molecule_id": molecule["molecule_id"], "smiles": molecule["smiles"],
                      "task": endpoint.name, **result})
    successes = sum(item["status"] == "ok" for item in calls)
    try:
        installed = importlib.metadata.version("admet-ai")
    except importlib.metadata.PackageNotFoundError:
        installed = "not-installed-or-injected"
    return {
        "status": "ok" if successes == len(candidates) else "partial_failure",
        "source": "admet_ai" if installed != "not-installed-or-injected" else "injected-test-predictor",
        "endpoint": endpoint.__dict__,
        "package_version": installed,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "successes": successes,
        "calls": calls,
        "budget": budget.__dict__,
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
