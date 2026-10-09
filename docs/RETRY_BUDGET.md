# Conservative retry reservation in the live agent

`EvaluationSession` now uses its configured cost for a tool call as the **maximum
allowable reservation**, not necessarily the post-call charge. `live_agent_run`
sets that amount to `endpoint.cost_units * adapter.max_attempts`. Before
running a model, action validation ensures that the remaining budget can afford
the whole reserved maximum. A returned finite cost in `[0, reserved]` is used
for settlement; a missing/malformed/out-of-range cost is conservatively charged
at the reserved maximum.

Cache hits require both `status=ok`, `cache_hit=true`, and `cost_units=0`.
Failed/invalid scores never become successful evaluations. This prevents an
unexpected retry sequence from overrunning the total registered cost budget
in serialized agent runs.

Tradeoff: a cache hit may be rejected before lookup when the remaining balance
cannot reserve the full maximum. A future improvement is a separate trusted
cache lookup before authorization and a durable journal recording retry attempts.
LLM token expense remains separate and is not covered by this budget guard.
