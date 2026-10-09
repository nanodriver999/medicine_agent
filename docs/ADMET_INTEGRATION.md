# ADMET-AI live integration (opt-in)

The official [ADMET-AI repository](https://github.com/swansonk14/admet_ai)
documents v2 Python usage:

```python
from admet_ai import ADMETModel
model = ADMETModel()
prediction = model.predict(smiles="CCO")
```

For a single SMILES, current documented output is a property-name-to-value dictionary.
The adapter in `amo.admet` is deliberately lazy-loaded so offline CI does not download model weights.

## Live run (manual; not CI)

1. In a separate environment install `pip install admet-ai` and record resolved package versions.
2. Invoke the real model once and inspect its actual property names, units, directions, supported tasks, and score meaning.
3. Construct `Endpoint(name=..., direction=..., unit=..., revision=...)` using **verified metadata** (do not silently guess direction from a column name).
4. Run ten distinct canonical SMILES through `ADMETAdapter` and record failures, model revision, wall clock time and cache hits.
5. Preserve the actual versioned model output separately from fixture results; never claim clinical safety or experimental validation.

A fake predictor is used only for API-contract tests. **No real ADMET-AI model was run by adding this adapter.**

### Known limitation

`ADMETModel.predict` may require downloads and memory, and current v2 models differ from
the v1 paper/server. The adapter currently handles one SMILES at a time; a batch adapter,
timeout worker and retry policy need separate integration testing.

The `hERG` test endpoint is a **fake dictionary key used in contract tests**, not proof
of an installed model's real endpoint name, units, direction, or calibration.
