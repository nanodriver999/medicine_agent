# Quality gates, known blockers and future development

Last updated: 2026-10-10. Only claim checks that actually ran.

## Completed and CI verified

1. Software-only: RDKit QED and SA, SMILES cleaning, properties, fingerprints, Pareto/diversity, missing values, budget guard.
2. Synthetic benchmark: 3 policies (fixed, rules, **placeholder agent**) × 3 seeds; deterministic offline fitness, CSV/JSON; score and cost curve.
3. Local offline interruption/resume contract and strict action rejection tests.
4. Real *input acquisition*: ChEMBL public API returned **120 unique canonical structures**; CI verified clean dataset, source SHA256 and a nine-run **synthetic** software benchmark.
5. Streamlit UI code and dependency installed by optional extras; the browser UI itself has not been manually smoke tested.

## Not verified / not completed

- **Real ADMET:** no actual pretrained ADMET-AI weights inference has passed a 10+ candidate integration smoke; endpoint semantics, units, revision and inference resource needs must be checked from live installed model.
- **True agent comparison:** default policy name `agent` in `amo compare` is a synthetic heuristic, not Strands. `amo agent-live` is opt-in but has only fake-driver tests. Must test an actual configured OpenAI-compatible LLM, bounded steps, errors, wall-time and token cost accounting.
- **Fairness:** real fixed/rules/agent benchmark must run with identical molecular pool, same ADMET endpoint/revision/normalization, separate cold caches and equivalent **total** cost units including LLM usage. Current synthetic runs do not imply real performance.
- **Operational correctness:** external calls cannot currently guarantee exactly-once billing on an interrupted call, and per-call hard timeouts/retry caps aren't fully integrated.
- **Provenance:** pin exact project dependency versions, RDKit contrib SA artifact/version, immutable dataset artifact SHA and exact model checkpoint revision for credible publication-level reproduction.
- **Phase B:** target-specific ChEMBL assay curation with unit/duplicate/censoring policy, scaffold split and blinded retrospective DMTA is research extension, not implemented.
- **Optional:** TxGemma Predict parser exists, but no real gated HF model inference or GPU validation has run.

## Next independently testable PRs

- P1: deterministic/real run data contracts, structured score status & provenance throughout; round-budget and model-call request journal.
- P1: bounded ADMET batch/retry/timeouts, endpoint inventory verification on selected installed version, >=10 real compounds.
- P1: live Strands step/time/token budget and disable unsupported tool calls; inspect actual logs for escaped injection.
- P1: fair fixed/rules/agent real benchmark, >=3 seeds with costs, coverage, confidence intervals and no hidden knowledge.
- P2: ChEMBL single-target assay dataset curation, scaffold leakage tests and hidden-label DMTA replay; no fabricated experimental result.
- P2: opt-in TxGemma GPU smoke, model revision & TDC task verification, isolated from ADMET score scales.

## Reproduction and evidence policy

Use `pytest -q`, `amo compare` (synthetic), and GitHub Actions job logs/artifacts for exact evidence. GitHub Actions artifacts are short-lived (currently 7 days) so publish a stable checksum-verified benchmark pool before claiming indefinite reproduction. No external model or clinical performance claim should be inferred from contract/mocked tests.
