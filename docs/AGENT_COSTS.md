# Agent evaluation cost accounting

`EvaluationSession` authorizes a call against its configured worst-case cost
**before** making a model request. After the model responds, the session charges:
- **0 cost units** for a well-formed successful tool response explicitly marked
  `cache_hit=true` and `cost_units=0`;
- the configured tool cost for normal successful executions;
- the configured cost for failed, malformed or unverifiable responses.

A cache hit still consumes a tool-call slot. The caller cannot change tool,
task, candidate ID, budget, or an execution's configured cost by supplying text
to the LLM. Model API/token billing is NOT included in these tool-level units.

This cost ledger reflects a **conservative accounting policy**; it does not
establish actual monetary provider charges, which need a separate provider
usage record. The current session assumes serialized tool calls. If concurrency
is introduced, budget validation+commit must be guarded atomically.
