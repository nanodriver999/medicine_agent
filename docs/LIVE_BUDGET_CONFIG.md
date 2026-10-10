# Live LLM budget configuration

Live Strands execution requires explicit input/output token pricing, pricing currency, a maximum per-round currency reservation and a total currency budget. The configured upper bound is a policy assumption and must include all actual provider billing components (cached, reasoning and retry usage where applicable). Missing or malformed values fail closed rather than run an unpriced call. `agent-live` still does not provide a verified hard total monetary ceiling across external ADMET calls; those are separately accounted as abstract units.
