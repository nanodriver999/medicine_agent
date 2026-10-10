# Strands currency preflight

`run_strands_round` can now reserve a configured LLM upper bound before invoking an agent and settle against provider-reported aggregate tokens. A missing upper bound prevents invocation in budgeted mode. Failures consume the reservation, while usage above the bound remains pending for investigation. The optional `agent_callable` supports offline contract tests. This does not independently establish provider prices or a complete maximum over cache/reasoning charges. Real-model execution remains unverified.
