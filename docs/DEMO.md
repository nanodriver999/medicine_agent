# Reproducible offline demonstration

```bash
python -m pip install -e '.[test,ui]'
pytest -q
amo prepare --input data/fixtures/smiles.csv --output /tmp/amo-prepared.csv
amo compare --input /tmp/amo-prepared.csv --budget 3 --seeds 42 43 44 --out outputs/compare
amo ui --runs outputs/compare
```

The comparison writes `comparison.json`, `comparison.csv` and `manifest.json`.
Every run uses the same input CSV, numeric budget and seed across policies.

**Scientific limitations:** the fixture oracle uses a deterministic SMILES hash and
is not an ADMET model. The current `agent` policy is a seeded simulated choice;
it does not demonstrate Strands or LLM behavior. Comparing these test modes
validates pipelines and basic budget parity, not improved medicinal chemistry.
Use real ADMET-AI and a live Strands model plus model-cost accounting before
claiming scientifically meaningful policy comparisons.
