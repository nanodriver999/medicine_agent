"""Fail-closed integrity gate before comparing model evaluation policies.

Identical model identity, candidate population, seed, limits and cache
protocol are required. Report a comparison as incomplete unless token costs
are explicitly measured for the agent and the baselines.
"""
from __future__ import annotations
import hashlib
import json
import math

def fingerprint_pool(rows):
    items = sorted((r["molecule_id"], r["smiles"]) for r in rows)
    if len(items) != len({key for key, _ in items}):
        raise ValueError("duplicate molecule IDs")
    return hashlib.sha256(json.dumps(items, separators=(",", ":")).encode()).hexdigest()

def verify_comparison(runs):
    if not isinstance(runs, list) or len(runs) < 2:
        raise ValueError("at least two runs required")
    required = ("policy", "seed", "pool_sha256", "model_revision", "endpoint",
                "budget_units", "cache_protocol", "evaluation_cost_units")
    for run in runs:
        if not isinstance(run, dict) or any(k not in run for k in required):
            raise ValueError("missing required run provenance")
        for key in ("budget_units", "evaluation_cost_units"):
            value = run[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("invalid cost or budget")
            if key == "evaluation_cost_units" and value > run["budget_units"]:
                raise ValueError("overspent evaluation budget")
    for key in ("seed", "pool_sha256", "model_revision", "endpoint",
                "budget_units", "cache_protocol"):
        if len({json.dumps(x[key], sort_keys=True) for x in runs}) != 1:
            raise ValueError("unequal benchmark conditions: " + key)
    if len({x["policy"] for x in runs}) != len(runs):
        raise ValueError("duplicate policy")
    # Evaluation cost units are synthetic budget weights by default; LLM
    # cost units may represent currency. They cannot be summed unless a
    # pre-declared, matching conversion has been applied to both.
    cost_units_match = all(
        x.get("evaluation_cost_basis") == x.get("llm_cost_basis") ==
        x.get("budget_cost_basis") and
        isinstance(x.get("budget_cost_basis"), str) and
        bool(x["budget_cost_basis"].strip())
        for x in runs
    )
    total_cost_verified = cost_units_match and all(
        isinstance(x.get("llm_cost_units"), (int, float))
        and not isinstance(x.get("llm_cost_units"), bool)
        and math.isfinite(x["llm_cost_units"]) and x["llm_cost_units"] >= 0
        and x["evaluation_cost_units"] + x["llm_cost_units"] <= x["budget_units"]
        for x in runs
    )
    return {
        "conditions_match": True,
        "total_cost_comparable": total_cost_verified,
        "cost_units_match": cost_units_match,
        "policy_count": len(runs),
        "status": ("comparable" if total_cost_verified else
                   "incompatible_cost_units" if not cost_units_match else
                   "incomplete_llm_cost"),
        "warning": "Comparability is a necessary condition, not proof of biological validity.",
    }
