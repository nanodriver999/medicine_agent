# Development roadmap and evidence gates

The repository follows `agentic_molecular_optimization_v2_implementation_test_plan.md`.

| Stage | Deliverable | Evidence |
| --- | --- | --- |
| PR 1 | Offline RDKit, Pareto, synthetic fixture policies | pytest and offline CLI CI |
| PR 2 | SQLite cache, server-enforced agent action schemas, 3x3 comparison | pytest contract/regression CI |
| PR 3 | SA score, real ADMET-AI adapter, endpoint metadata and smoke | opt-in live model smoke; no synthetic substitution |
| PR 4 | Strands agent policy, strict tool approvals, trace, retry, budget accounting | injected malformed and adversarial tool actions |
| PR 5 | CLI comparison, Streamlit, fair-budget metrics, provenance, resumability | full 3x3 fixture CI and manual UI |
| Later | TxGemma Predict, ChEMBL prospective-hidden/replay study | separate benchmarks with provenance |

Never present offline-fixture values or placeholder policy as a scientific model or LLM agent.
