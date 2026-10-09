# Optional Strands agent execution

The Strands SDK supports Python `Agent` with custom `@tool` functions and an
OpenAI-compatible model provider. The module `amo.agent_policy` exposes
`build_strands_agent(session, model)` and `run_strands_round(session, model)`.

```python
# Opt-in demonstration; model calls are real and can incur usage charges.
from strands.models.openai import OpenAIModel
from amo.agent_policy import EvaluationSession, run_strands_round
from amo.core import Budget

# Use an explicitly configured API key and model, never commit keys.
model = OpenAIModel(model_id="YOUR_MODEL",
    client_args={"api_key": "YOUR_SECRET", "base_url": "YOUR_OPENAI_COMPATIBLE_URL"})
session = EvaluationSession(
    {"mol_1": "CCO"},
    evaluator=lambda smiles, tool, task: {"status": "ok", "value": 0.5, "source": "test_only"},
    tasks={"offline_fixture": {"synthetic"}},
    costs={"offline_fixture": 1.0},
    budget=Budget(1.0, 1),
)
report = run_strands_round(session, model)
```

The above stub evaluator is **only a software exercise**, not genuine ADMET.
A real evaluator should call `ADMETAdapter.evaluate` and verify the configured endpoint.
The model receives ONLY one tool and cannot bypass the code-side budget and allowlist.
Any failed or malformed model outputs are recorded as failures.

Run `pip install 'strands-agents[openai]'` separately to enable it.
Strands SDK and LLM integration smoke tests need a configured accessible model
and are **not run by offline CI**. Follow-up: integrate with CLI, record token cost,
limit agent loop iterations and wall time, and compare against baselines without
conflating the current placeholder `agent` mode with live LLM policy.
