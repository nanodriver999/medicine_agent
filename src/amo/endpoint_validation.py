"""Validate actual installed ADMET model response keys before execution."""
from __future__ import annotations
import math


def assert_endpoint_present(inventory: dict, name: str) -> None:
    if not isinstance(inventory, dict) or not isinstance(inventory.get("endpoints"), list):
        raise ValueError("invalid endpoint inventory")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("endpoint name required")
    matches = [item for item in inventory["endpoints"]
               if isinstance(item, dict) and item.get("name") == name]
    if len(matches) != 1 or matches[0].get("numeric_finite") is not True:
        raise ValueError("selected endpoint missing or not numeric")
    value = matches[0].get("sample_value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("invalid endpoint probe value")
