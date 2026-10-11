"""Paired-seed bootstrap intervals for policy comparison; no biological claims."""
from __future__ import annotations
import math
import random
import statistics


def paired_bootstrap(runs: list[dict], *, metric: str, policy_a: str,
                     policy_b: str, draws: int = 2000, seed: int = 2026,
                     confidence: float = 0.95) -> dict:
    if not isinstance(metric, str) or not metric or policy_a == policy_b:
        raise ValueError("provide distinct policies and a metric")
    if type(draws) is not int or not 100 <= draws <= 100000:
        raise ValueError("draws must be within 100..100000")
    if not 0 < confidence < 1 or not math.isfinite(confidence):
        raise ValueError("confidence must be between 0 and 1")
    values = {policy_a: {}, policy_b: {}}
    for row in runs:
        policy = row.get("policy")
        if policy not in values:
            continue
        run_seed = row.get("seed")
        if type(run_seed) is not int or run_seed in values[policy]:
            raise ValueError("seed must be unique per policy")
        value = row.get(metric)
        if value is not None and (isinstance(value, bool) or
                                  not isinstance(value, (int, float)) or
                                  not math.isfinite(value)):
            raise ValueError("metric must be finite numeric or null")
        values[policy][run_seed] = value
    if set(values[policy_a]) != set(values[policy_b]):
        raise ValueError("unpaired policy seeds")
    seeds = sorted(values[policy_a])
    if len(seeds) < 3:
        raise ValueError("at least three paired seeds required")
    differences = []
    for run_seed in seeds:
        a, b = values[policy_a][run_seed], values[policy_b][run_seed]
        if a is None or b is None:
            raise ValueError("missing observations cannot be imputed")
        differences.append(float(a - b))
    rng = random.Random(seed)
    n = len(differences)
    samples = sorted(sum(rng.choice(differences) for _ in range(n))/n
                     for _ in range(draws))
    alpha = (1-confidence)/2
    lo = samples[max(0, int(alpha * draws))]
    hi = samples[min(draws-1, int((1-alpha) * draws))]
    return {"policy_a": policy_a, "policy_b": policy_b, "metric": metric,
            "paired_seeds": n, "seed_values": seeds, "mean_difference": statistics.mean(differences),
            "confidence": confidence, "interval_low": lo, "interval_high": hi,
            "bootstrap_draws": draws, "bootstrap_rng_seed": seed,
            "method": "paired_percentile_bootstrap",
            "scope": "descriptive interval across the tested seeds only",
            "warning": "Three seeds give highly unstable intervals; no biological efficacy inference."}
