# Agentic Molecular Optimization (research prototype)

Implements the first offline screening slice of the v2.0 plan. This is a research/education tool and does **not** establish drug activity or safety.

```bash
python -m pip install -e '.[test]'
pytest -q
amo prepare --input data/fixtures/smiles.csv --output /tmp/amo-prepared.csv
amo score --input /tmp/amo-prepared.csv --out /tmp/amo-score
amo run --input /tmp/amo-prepared.csv --policy fixed --budget 3 --out /tmp/amo-fixed
amo run --input /tmp/amo-prepared.csv --policy rules --budget 3 --out /tmp/amo-rules
amo run --input /tmp/amo-prepared.csv --policy agent --budget 3 --out /tmp/amo-agent
```

The `agent` name currently refers only to a deterministic placeholder selector, **not a live LLM**. The SHA-256-based `fixture_risk` is a software test fixture and **not** an ADMET score. `docs/IMPLEMENTATION_STATUS.md` lists unfinished work.
