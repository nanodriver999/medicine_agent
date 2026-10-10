# Real-model deterministic baselines

`run_baseline` evaluates `fixed` and `rules` policy candidates using the same real or injected ADMET adapter contract, cost reservation and error isolation. Tests use injected predictor outputs, not real ADMET inference. A live agent comparison still needs the same pool, revision, cache conditions, and a budget that includes LLM usage.
