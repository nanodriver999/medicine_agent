# LLM usage accounting

The ledger accepts provider-reported token counts only and calculates cost units from explicitly supplied prices per million tokens. No prices, token counts, or model capabilities are inferred. The ledger is not yet wired to the actual Strands provider response; missing usage remains an explicit incomplete state. Provider usage may omit cache-write/read and other billing categories; audit these before treating the total as a complete invoice.
