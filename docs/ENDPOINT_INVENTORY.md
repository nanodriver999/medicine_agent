# Opt-in ADMET endpoint inventory

```bash
pip install admet-ai
amo admet-inspect --smiles CCO --out outputs/admet_endpoint_inventory.json
```

This command runs **one real ADMETModel prediction** and records only the
property names, numeric sample outputs, installed package version and timestamp.
It does NOT infer the unit, safety direction, calibration, task semantics or
exact model-weight revision from the property name. These fields are explicitly
`UNVERIFIED` and must be checked against the model's task documentation
before using `amo admet-smoke --endpoint ...`.

The default CI exercises only injected dictionaries and does not download
ADMET-AI weights. Real inference may need substantial network/RAM and should
remain an explicit opt-in.
