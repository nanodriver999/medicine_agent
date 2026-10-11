"""Inspect actual ADMET output fields without assigning scientific semantics."""
from __future__ import annotations
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from numbers import Real
from pathlib import Path

from .core import standardize


def inspect_prediction(smiles: str, raw: dict) -> dict:
    canonical = standardize(smiles)
    if canonical is None:
        raise ValueError("invalid probe molecule")
    if not isinstance(raw, dict) or not raw:
        raise ValueError("ADMETModel.predict must provide a non-empty dict")
    endpoints = []
    for name, value in sorted(raw.items()):
        if not isinstance(name, str) or not name:
            raise ValueError("invalid endpoint name")
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            endpoints.append({"name": name, "numeric_finite": False, "sample_value": None})
        else:
            endpoints.append({"name": name, "numeric_finite": True, "sample_value": float(value)})
    try:
        version = importlib.metadata.version("admet-ai")
    except importlib.metadata.PackageNotFoundError:
        version = "unavailable"
    return {
        "probe_smiles": canonical,
        "package_version": version,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "endpoints": endpoints,
        "direction": "UNVERIFIED",
        "unit": "UNVERIFIED",
        "revision": "UNVERIFIED",
        "warning": "Observed API field names are not verified toxicity labels, units, directions, or calibrated risks.",
    }


def save_inventory(report: dict, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
