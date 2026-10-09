# Opt-in live ADMET-AI smoke run

Prepare an environment with sufficient CPU/RAM, network access for weights, and
an installed version of `admet-ai`. The smoke test is deliberately excluded
from default CI, because model downloads and inference can be substantial.

First confirm a specific property key and **its actual direction/units** from the
installed ADMET-AI version. Then:

```bash
pip install admet-ai
amo admet-smoke --input data/processed/chembl_pool_clean.csv \
  --endpoint VERIFIED_PROPERTY --direction min --unit VERIFIED_UNIT \
  --revision VERIFIED_MODEL_REVISION --count 10 --out outputs/admet-smoke
```

Record the real model revision in `--revision` (not just the Python package version).
The command generates `admet_smoke.json` and `calls.jsonl`, flags failures and
identifies the installed package. It does **not** make toxicity/safety claims.

Currently the CLI does not discover endpoint semantics automatically. A separate,
environment-verified endpoint inventory and batched/timeout-isolated inference are
required before unrestricted use. Unit tests inject a fake predictor, not actual model
weights; the real inference must be reported separately.
