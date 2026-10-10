# Provider call reservation bridge

An LLM provider invocation must reserve a defensible upper bound before dispatch. The injected `invoke` callback executes only after reservation, and `actual_cost` must parse verified usage in the same currency. On failure or missing usage, the reservation is conservatively spent. If usage exceeds the reserved amount or usage validation raises, the reservation remains pending and requires reconciliation; no silent refund is made.

**Scope:** this is a callable integration primitive, not yet wired into the live Strands agent API. Exact currency bounds depend on known input size, output caps, accurate model rates and billing categories. It is unsafe to claim an absolute provider-billing ceiling without those guarantees.
