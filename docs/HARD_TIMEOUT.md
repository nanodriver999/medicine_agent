# Optional subprocess deadline for ADMET predictions

The `amo admet-smoke` CLI exposes an explicit `--hard-timeout SECONDS` flag:

```bash
amo admet-smoke \
  --input data/processed/chembl_pool_clean.csv --count 10 \
  --endpoint VERIFIED_PROPERTY --direction min --unit VERIFIED_UNIT \
  --revision VERIFIED_MODEL_REVISION \
  --hard-timeout 120 --out outputs/live-admet-smoke
```

When enabled, each ADMET prediction uses a **fresh spawned subprocess** with
an enforced deadline. A timed-out worker is terminated and the adapter records
a failed prediction rather than guessing a score. The subprocess invocation
is an opt-in alternative to the default in-process adapter.

**Limitations:** spawning and loading ADMET-AI for every molecule is expensive.
This path is intended for safety-focused small smoke tests, not efficient
high-throughput batches. It does not independently track or kill any nested
processes started by model libraries, and can be unsuitable for GPU memory
sharing. Real-model inference remains opt-in and has not been verified in CI.

The default offline `amo compare` command never loads real ADMET model
weights or uses this timeout configuration.
