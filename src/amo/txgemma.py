"""Strict, opt-in TxGemma Predict task prompt and generated-answer contracts."""
from __future__ import annotations
from dataclasses import dataclass
import math
import re
from typing import Callable

from .core import standardize


def build_tdc_prompt(template: str, smiles: str) -> str:
    """Use an official task template supplied by caller; no invented prompts."""
    canonical = standardize(smiles)
    if canonical is None:
        raise ValueError("invalid SMILES")
    placeholder = "{Drug SMILES}"
    if not isinstance(template, str) or template.count(placeholder) != 1:
        raise ValueError("a verified TDC task template with one SMILES placeholder is required")
    return template.replace(placeholder, canonical)


def parse_classification(text: str, labels: tuple[str, ...] = ("A", "B")) -> dict:
    """Accept exactly one configured label; no substring or explanation coercion."""
    if not isinstance(text, str):
        return {"status": "parse_error", "value": None}
    normalized = text.strip()
    if re.fullmatch(r"\([A-Za-z]\)|[A-Za-z]", normalized):
        normalized = normalized.strip("()").upper()
        if normalized in labels:
            return {"status": "ok", "value": normalized,
                    "unit": "categorical", "calibrated_probability": False}
    return {"status": "parse_error", "value": None}


def parse_regression(text: str) -> dict:
    """Only a standalone finite number can be a numerical prediction."""
    if not isinstance(text, str):
        return {"status": "parse_error", "value": None}
    stripped = text.strip()
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", stripped):
        return {"status": "parse_error", "value": None}
    value = float(stripped)
    if not math.isfinite(value):
        return {"status": "parse_error", "value": None}
    return {"status": "ok", "value": value}


@dataclass(frozen=True)
class TxTask:
    name: str
    template: str
    kind: str
    revision: str

    def __post_init__(self):
        if not self.name or not self.revision or self.kind not in {"classification", "regression"}:
            raise ValueError("invalid task descriptor")
        if self.template.count("{Drug SMILES}") != 1:
            raise ValueError("invalid official prompt template")


def predict(smiles: str, task: TxTask, generator: Callable[[str], str]) -> dict:
    """Generated continuation ONLY; never pass full prompt+answer to parser."""
    prompt = build_tdc_prompt(task.template, smiles)
    try:
        continuation = generator(prompt)
        result = (parse_classification(continuation) if task.kind == "classification"
                  else parse_regression(continuation))
        return {**result, "source": "txgemma_predict", "task": task.name,
                "model_revision": task.revision,
                "raw_continuation": continuation if isinstance(continuation, str) else None}
    except Exception as exc:
        return {"status": "failed", "value": None, "source": "txgemma_predict",
                "task": task.name, "model_revision": task.revision,
                "error_code": type(exc).__name__}
