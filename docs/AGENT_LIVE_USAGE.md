# Agent live usage reporting

Configure `LLM_INPUT_UNITS_PER_MILLION` and `LLM_OUTPUT_UNITS_PER_MILLION`
with *explicitly verified* cost-unit prices for the configured LLM model.
During actual Strands execution, aggregated provider-reported token counts
are recorded into the LLM ledger and surfaced in `agent_run.json`.
Without these prices, token metrics may be present but monetary cost remains
unverified. Prices here are cost units rather than guaranteed provider currency.
Cache-read/write charges, any reasoning-specific billing, and other provider
billing dimensions require separate verification before total-cost fairness can
be claimed. No real LLM was called by CI.
