# Bounded prediction retries

`ADMETAdapter` accepts `max_attempts` (1–5, default 1),
`retry_delay_seconds` (0–60, default 0), and an injectable sleep hook.
Only Python `TimeoutError` or `ConnectionError` from the predictor are retried.
Malformed data, unknown endpoint names, and invalid/nonfinite scores fail
immediately. No failure is turned into a guessed risk score.

The result records `attempts`, cumulative elapsed time and conservative
`cost_units = attempts * endpoint.cost_units`. Verified cache hits use
`cost_units=0`. Failed requests can still consume provider resources, so each
attempt is conservatively included in the accounting ledger.

**Important limits:** these are *retries of reported transient exceptions*, not
hard execution timeouts. Synchronous model predictions that hang inside native
code cannot be interrupted by this adapter. A subprocess-isolated worker with
a hard wall-clock deadline and durable pre-call journal remains necessary for
robust real-model execution. Retry attempts must fit an enclosing controller's
reserved budget; the standalone smoke/agent callers currently do not reserve
the maximum retry amount, so leave `max_attempts=1` when invoking those paths.
