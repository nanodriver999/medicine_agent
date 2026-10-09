# Implementation status

This is an incremental implementation of the attached v2.0 research plan.

## PR 1: offline screening foundation

- RDKit canonicalization, validation, deduplication, descriptors, Morgan fingerprints.
- Pareto dominance/frontier and mean pairwise Tanimoto diversity.
- Hard evaluation budget and three **offline** scheduling modes.
- Explicit synthetic fixture oracle for deterministic software tests; it is NOT ADMET-AI.
- Prepare, score, run CLI; JSON/CSV and call ledger; pytest + CI.

## Important limitations

- `agent` is currently a seeded **deterministic placeholder policy**, not an LLM or Strands integration. Do not cite its performance as agentic performance.
- SA Score, real ADMET-AI inference, endpoint semantics, provenance manifest, persistent cache, robust retry/resume, fair multi-seed comparison and Streamlit UI remain to be implemented.
- Input fixture is a hand-curated smoke set, not a benchmark dataset; no biological or toxicity conclusions are possible.
- Do not confuse synthetic fixture risk scores with experimental outcomes.

## Next engineering stages

1. SA Score and explicitly versioned ADMET-AI adapter with cache, endpoint contract tests and failure isolation.
2. Validated LLM/Strands action selection and budget guards, with deterministic fallback.
3. Equitable 3-policy x 3-seed comparison, run manifests, reporting, Streamlit UI and resume tests.
4. Optional TxGemma Predict and retrospective target-specific ChEMBL experiment.
