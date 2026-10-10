# Agent execution limits

The server rejects tool evaluations beyond a monotonic wall-clock deadline or a maximum number of proposed actions, including invalid proposals. These guards do not interrupt an LLM call already blocking or a model subprocess that has started. LLM token costs still need separate accounting and verification.
