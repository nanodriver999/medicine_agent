"""Opt-in ADMET-AI prediction adapter.

The current ADMET-AI v2 package exposes ADMETModel().predict(smiles=...).
No model is imported, downloaded, or executed in offline fixture tests.
Endpoint semantics must be explicitly recorded from the installed model.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import time
from typing import Callable, Any

from .core import standardize
from .runtime import ScoreCache


@dataclass(frozen=True)
class Endpoint:
    name: str
    direction: str
    unit: str
    revision: str
    cost_units: float = 1.0

    def __post_init__(self):
        if not self.name or not self.revision or not self.unit:
            raise ValueError("endpoint identity, unit and model revision required")
        if self.direction not in {"min", "max"}:
            raise ValueError("endpoint direction must be explicit")
        if not math.isfinite(self.cost_units) or self.cost_units < 0:
            raise ValueError("invalid endpoint cost")


class ADMETAdapter:
    """One endpoint at a time; return structured failure, not a fabricated value."""

    def __init__(self, endpoint: Endpoint, *, predictor: Callable[[str], Any] | None = None,
                 cache: ScoreCache | None = None,
                 max_attempts: int = 1, retry_delay_seconds: float = 0.0,
                 sleep: Callable[[float], None] = time.sleep):
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 5:
            raise ValueError("max_attempts must be an integer in [1, 5]")
        if not math.isfinite(retry_delay_seconds) or retry_delay_seconds < 0 or retry_delay_seconds > 60:
            raise ValueError("invalid bounded retry delay")
        self.max_attempts, self.retry_delay_seconds, self.sleep = max_attempts, retry_delay_seconds, sleep
        self.endpoint, self.cache = endpoint, cache
        if predictor is None:
            from admet_ai import ADMETModel
            model = ADMETModel()
            predictor = lambda smiles: model.predict(smiles=smiles)
        self.predictor = predictor

    def evaluate(self, smiles: str) -> dict:
        canonical = standardize(smiles)
        if canonical is None:
            return {"status": "invalid", "value": None, "cost_units": 0, "cache_hit": False}
        e = self.endpoint
        cache_key = ScoreCache.key(canonical, "admet_ai", e.name, e.revision)
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return {**cached, "cache_hit": True, "cost_units": 0, "latency_ms": 0}
        start = time.perf_counter()
        attempts = 0
        for attempt in range(1, self.max_attempts + 1):
            attempts = attempt
            try:
                raw = self.predictor(canonical)
                if not isinstance(raw, dict) or e.name not in raw:
                    raise ValueError("ADMET prediction endpoint missing")
                value = raw[e.name]
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value)):
                    raise ValueError("ADMET prediction must be a finite numeric value")
                result = {"status": "ok", "value": float(value), "endpoint": e.name,
                          "direction": e.direction, "unit": e.unit, "model_revision": e.revision,
                          "source": "admet_ai", "cache_hit": False,
                          "attempts": attempts, "cost_units": attempts * e.cost_units,
                          "latency_ms": round((time.perf_counter() - start) * 1000, 3)}
                if self.cache is not None:
                    self.cache.put(cache_key, result)
                return result
            except (TimeoutError, ConnectionError) as exc:
                # Only transient transport/timeout errors are eligible for retries.
                # Model schema errors must fail closed without retrying.
                error_code = type(exc).__name__
                if attempt < self.max_attempts:
                    self.sleep(self.retry_delay_seconds)
                    continue
            except Exception as exc:
                error_code = type(exc).__name__
                break
        return {"status": "failed", "value": None, "endpoint": e.name,
                "source": "admet_ai", "cache_hit": False, "attempts": attempts,
                "cost_units": attempts * e.cost_units,
                "latency_ms": round((time.perf_counter() - start) * 1000, 3),
                "error_code": error_code}
