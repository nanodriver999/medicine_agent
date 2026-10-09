"""Atomic offline checkpoint/restart without duplicate fixture evaluations.

Only the deterministic offline fixture is supported. Real paid model calls need
idempotency tokens and/or durable before-call journaling to guarantee billing.
"""
from __future__ import annotations
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path

from .core import Budget, choose, descriptors, offline_oracle, prepare, pareto_front, save_run


def _atomic_json(path: Path, value: dict):
    partial = path.with_suffix(path.suffix + ".tmp")
    with partial.open("w", encoding="utf-8") as fp:
        json.dump(value, fp, indent=2)
        fp.flush()
        os.fsync(fp.fileno())
    os.replace(partial, path)


def run_resumable(rows: list[dict], out: str | Path, *, policy: str,
                  seed: int = 42, budget_units: int = 5,
                  max_new_calls: int | None = None) -> dict:
    if budget_units < 0 or max_new_calls is not None and max_new_calls < 0:
        raise ValueError("negative budget")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    scored = [{"molecule_id": item["molecule_id"],
               **descriptors(item["smiles"])} for item in prepare(rows)]
    ordered = choose(scored, policy, seed)
    canonical = json.dumps(scored, sort_keys=True, separators=(",", ":"))
    identity = {"policy": policy, "seed": seed, "budget_units": budget_units,
                "candidate_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
                "oracle": "sha256-offline-fixture-v1"}
    path = out / "checkpoint.json"
    if path.exists():
        checkpoint = json.loads(path.read_text(encoding="utf-8"))
        if checkpoint.get("identity") != identity:
            raise ValueError("resume request does not match checkpoint identity")
        evaluated = list(checkpoint["evaluated"])
        calls = list(checkpoint["calls"])
    else:
        evaluated, calls = [], []
    if len(calls) != len(evaluated):
        raise ValueError("checkpoint ledger corrupt")
    if len({r["smiles"] for r in evaluated}) != len(evaluated):
        raise ValueError("duplicate cache entries in checkpoint")
    budget = Budget(budget_units, budget_units, len(calls), len(calls))
    seen = {r["smiles"] for r in evaluated}
    new_calls = 0
    for candidate in ordered:
        if candidate["smiles"] in seen:
            continue
        if not budget.permits(1) or (max_new_calls is not None and new_calls >= max_new_calls):
            break
        predicted = {**candidate, "fixture_risk": offline_oracle(candidate["smiles"]),
                     "fixture_risk_status": "ok",
                     "fixture_risk_source": "offline-fixture"}
        budget.debit(1)
        evaluated.append(predicted)
        calls.append({"molecule_id": candidate["molecule_id"], "tool": "offline-fixture",
                      "status": "ok", "cost_units": 1, "cache_hit": False})
        seen.add(candidate["smiles"])
        new_calls += 1
        _atomic_json(path, {"identity": identity, "evaluated": evaluated, "calls": calls})
    remaining = any(candidate["smiles"] not in seen for candidate in ordered)
    complete = not remaining or not budget.permits(1)
    result = {"policy": policy, "seed": seed, "molecules": scored,
              "evaluated": evaluated, "calls": calls,
              "pareto": pareto_front(evaluated, {"qed": "max", "fixture_risk": "min"}),
              "budget": asdict(budget), "mode": "offline-fixture", "complete": complete,
              "warning": "Offline synthetic fixture only; not real ADMET/LLM inference."}
    save_run(result, out)
    _atomic_json(out / "manifest.json", {"identity": identity, "complete": complete,
                                         "restarted": path.exists(), "source": "offline-fixture"})
    return result
