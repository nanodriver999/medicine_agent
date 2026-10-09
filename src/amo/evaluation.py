"""Offline policy comparison with explicit synthetic-oracle labeling."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import platform
import statistics
from rdkit import rdBase
from .core import run, diversity


def run_comparison(rows: list[dict], *, seeds=(42, 43, 44),
                   policies=("fixed", "rules", "agent"), budget=5) -> dict:
    """Identical pool and budget; seed is held constant across policies."""
    if not seeds or not policies or budget < 0:
        raise ValueError("invalid comparison configuration")
    items = []
    for seed in seeds:
        for policy in policies:
            result = run(rows, policy=policy, seed=seed,
                         max_cost_units=budget, max_tool_calls=budget)
            measured = result["evaluated"]
            values = [r["qed"] - r["fixture_risk"] for r in measured]
            items.append({
                "policy": policy, "seed": seed, "mode": "offline-fixture",
                "evaluated": len(measured),
                "cost_units": result["budget"]["used_cost_units"],
                "best_fixture_objective": max(values) if values else None,
                "pareto_count": len(result["pareto"]),
                "diversity": diversity([r["smiles"] for r in measured]),
            })
    aggregates = []
    for policy in policies:
        vals = [r["best_fixture_objective"] for r in items
                if r["policy"] == policy and r["best_fixture_objective"] is not None]
        aggregates.append({"policy": policy, "n": len(vals),
                           "mean_best_fixture_objective": statistics.mean(vals) if vals else None,
                           "std_best_fixture_objective": statistics.stdev(vals) if len(vals) > 1 else None})
    return {"runs": items, "summary": aggregates,
            "warning": "Synthetic oracle: software comparison only; not evidence of drug activity."}


def export_comparison(report: dict, out: str | Path, input_path: str | Path | None = None) -> None:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparison.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (out / "comparison.csv").open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(report["runs"][0]) if report["runs"]
                                else ["policy", "seed"])
        writer.writeheader()
        writer.writerows(report["runs"])
    manifest = {"mode": "offline-fixture", "python": platform.python_version(),
                "rdkit": rdBase.rdkitVersion,
                "input_sha256": hashlib.sha256(Path(input_path).read_bytes()).hexdigest()
                if input_path is not None else None,
                "scientific_scope": "synthetic benchmark only"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
