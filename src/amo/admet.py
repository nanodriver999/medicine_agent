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
                 cache: ScoreCache | None = None):
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
        try:
            raw = self.predictor(canonical)
            if not isinstance(raw, dict) or e.name not in raw:
                raise ValueError("ADMET prediction endpoint missing")
            value = raw[e.name]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("ADMET prediction must be a finite numeric value")
            result = {"status": "ok", "value": float(value), "endpoint": e.name,
                      "direction": e.direction, "unit": e.unit, "model_revision": e.revision,
                      "source": "admet_ai", "cache_hit": False,
                      "cost_units": e.cost_units,
                      "latency_ms": round((time.perf_counter() - start) * 1000, 3)}
            if self.cache is not None:
                self.cache.put(cache_key, result)
            return result
        except Exception as exc:
            # Exceptions can contain server data; do not leak untrusted exception text.
            return {"status": "failed", "value": None, "endpoint": e.name,
                    "source": "admet_ai", "cache_hit": False,
                    "cost_units": e.cost_units,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 3),
                    "error_code": type(exc).__name__}
