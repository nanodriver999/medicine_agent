# Retry-aware ADMET smoke budget

For each external prediction, `run_smoke` calculates the worst-case adapter cost as endpoint.cost_units × max_attempts. It reserves this amount before invoking the adapter and records the actual attempts and cost after completion, including transient errors. The smoke total budget scales to `count × maximum_per_call`; it is an evaluation-cost accounting limit, not a currency/billing guarantee. Offline CI uses injected predictors only, not actual ADMET weights.
