# Strands token usage capture

For a successful agent call, capture `AgentResult.metrics.accumulated_usage` (`inputTokens`, `outputTokens`, optionally `totalTokens`). Malformed and missing fields are kept as explicit unverified states. An optional `LLMUsageLedger` records provider-returned totals using independently configured prices. This does not assume model pricing, nor account for cache billing categories automatically; no live LLM was exercised by CI. Official SDK reference: https://strandsagents.com/docs/user-guide/sdk/observability-evaluation/metrics/.
