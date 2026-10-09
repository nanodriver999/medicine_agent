# Medicine Agent — Agentic Molecular Optimization

Research-oriented **budget-aware molecular evaluation and candidate selection** using existing computational tools. This repository does **not** establish clinical safety, measured activity, or drug efficacy.

## What works today

- RDKit SMILES canonicalization, duplicate rejection, QED/MW/cLogP/TPSA/SA descriptors, Morgan fingerprints.
- Hard-coded budget checks, Pareto frontier, structural diversity, seeded offline `fixed` and `rules` baselines, and a **simulated** `agent` baseline.
- Strict agent tool allowlisting; optional Strands agent interface and ADMET-AI prediction adapter.
- Deterministic synthetic fixture experiment over multiple seeds, CSV/JSON/manifests, optional Streamlit UI.
- Atomic offline checkpoint/resume.
- ChEMBL public API molecule-pool acquisition with source/time/checksum recording; a live data workflow has verified **120 unique valid structures** and nine **synthetic** benchmark runs.

**Crucial:** The default `agent` benchmark is a deterministic placeholder, **not** evidence of a live LLM. The `fixture_risk` number is a synthetic SHA-256-derived oracle, **not** an ADMET model result.

## Quickstart (Python 3.11 recommended)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test,ui]'
pytest -q
amo prepare --input data/fixtures/smiles.csv --output /tmp/amo-prepared.csv
amo compare --input /tmp/amo-prepared.csv --budget 3 --seeds 42 43 44 --out outputs/compare
amo ui --runs outputs/compare
```

On Windows PowerShell use `.venv\\Scripts\\Activate.ps1`.

## Optional real-data and model integrations

```bash
python scripts/fetch_chembl_pool.py --count 120 --out data/processed/chembl_pool.csv
amo prepare --input data/processed/chembl_pool.csv --output data/processed/chembl_pool_clean.csv
```

See [ADMET smoke](docs/ADMET_SMOKE.md), [live agent](docs/AGENT_LIVE.md), [TxGemma](docs/TXGEMMA.md), [ChEMBL data](docs/DATA_SOURCE.md), and [benchmark interpretation](docs/METRICS.md). These real model executions require their actual optional dependencies, weights, model-specific metadata, and (for an LLM) an authorized endpoint. They have **not** been validated by ordinary CI.

## Project status and follow-on work

Read [quality and reproducibility gates](docs/QUALITY_GATES.md), [roadmap](docs/ROADMAP.md) and [initial implementation notes](docs/IMPLEMENTATION_STATUS.md). The original build spec lives outside this repository in the supplied `agentic_molecular_optimization_v2_implementation_test_plan.md`.

This repository started from the [Luna Chat Coder template](https://github.com/Osteoporosis/luna-chat-coder). Its development-specific instructions remain at [AGENTS.md](AGENTS.md) and [the embedded skill](.agents/skills/luna-chat-coder/SKILL.md).
