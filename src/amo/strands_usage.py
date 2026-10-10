"""Strict extraction of aggregated Strands AgentResult usage."""
from __future__ import annotations

def extract_strands_usage(result):
    metrics = getattr(result, "metrics", None)
    usage = getattr(metrics, "accumulated_usage", None)
    if not isinstance(usage, dict):
        return {"status": "missing_provider_usage"}
    input_tokens, output_tokens = usage.get("inputTokens"), usage.get("outputTokens")
    if any(type(n) is not int or n < 0 for n in (input_tokens, output_tokens)):
        return {"status": "invalid_provider_usage"}
    total = usage.get("totalTokens")
    if total is not None and (type(total) is not int or total != input_tokens + output_tokens):
        return {"status": "invalid_provider_usage"}
    return {"status": "ok", "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_metrics_present": any(k in usage for k in ("cacheReadInputTokens", "cacheWriteInputTokens"))}
