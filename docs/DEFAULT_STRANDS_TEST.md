# Default Strands path contract test

An in-process fake Strands SDK exercises the actual `live_agent_run(..., driver=None)` branch, including model setup, tool evaluation, budget reservation and settlement, provider usage extraction and incomplete-usage propagation. No external LLM or ADMET weights are used; this is a software-path regression test rather than an online model integration or scientific performance result.
