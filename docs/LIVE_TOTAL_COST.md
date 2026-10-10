# Live run total-cost report

The agent report records `total_cost` separately from evaluation units and LLM usage. `LLM_PRICING_CURRENCY` and `EVALUATION_CURRENCY_PER_COST_UNIT` are explicit user-provided pricing assumptions, not verified provider invoices. Missing inputs or provider usage produce incomplete status. The total is recorded after execution; tool admission only limits abstract evaluation units, not complete monetary spending.
