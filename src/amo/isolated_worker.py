"""Spawn-isolated prediction with a hard wall-clock deadline.

A fresh subprocess is used for each call. This deliberately trades startup and
model-loading overhead for fault containment; persistent workers are future work.
"""
from __future__ import annotations
import math
import multiprocessing as mp
from queue import Empty
import time
from typing import Any


def _predict_admet(smiles: str) -> dict:
    from admet_ai import ADMETModel
    return ADMETModel().predict(smiles=smiles)


def _worker(output, callable_, smiles: str):
    try:
        output.put(("ok", callable_(smiles)))
    except BaseException as exc:
        # Never transmit exception messages; they may contain sensitive data.
        output.put(("error", type(exc).__name__))


def invoke_bounded(smiles: str, *, timeout_seconds: float = 120,
                   predictor=None) -> dict:
    """Run a picklable predictor with spawn and always terminate on timeout.

    The predictor parameter is for testing; production defaults to ADMET-AI.
    The result is an envelope, not a verified ADMET score. The adapter must
    still validate the endpoint and finite numeric prediction.
    """
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be finite and positive")
    context = mp.get_context("spawn")
    output = context.Queue(maxsize=1)
    process = context.Process(target=_worker, args=(output, _predict_admet if predictor is None else predictor, smiles))
    process.daemon = True
    try:
        process.start()
        process.join(timeout_seconds)
        if process.is_alive():
            process.terminate()
            process.join(2)
            if process.is_alive():
                process.kill()
                process.join(2)
            return {"status": "failed", "error_code": "HardTimeout", "value": None}
        try:
            outcome, payload = output.get(timeout=0.5)
        except Empty:
            return {"status": "failed", "error_code": "WorkerExited", "value": None}
        if outcome == "error":
            return {"status": "failed", "error_code": payload if str(payload).isidentifier() else "WorkerError", "value": None}
        if not isinstance(payload, dict):
            return {"status": "failed", "error_code": "InvalidWorkerResponse", "value": None}
        return {"status": "ok", "raw": payload}
    finally:
        if process.pid is not None and process.is_alive():
            process.kill()
            process.join()
        output.close()
        output.join_thread()


def predict_with_deadline(smiles: str, *, timeout_seconds: float = 120) -> dict:
    """Adapter-compatible raw prediction or typed exception for existing retry handling."""
    result = invoke_bounded(smiles, timeout_seconds=timeout_seconds)
    if result["status"] == "ok":
        return result["raw"]
    if result["error_code"] == "HardTimeout":
        raise TimeoutError("isolated worker exceeded deadline")
    raise RuntimeError("isolated model worker failed")
