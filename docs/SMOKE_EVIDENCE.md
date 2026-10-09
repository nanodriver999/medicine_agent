# Live inference evidence boundary

The `amo admet-smoke` command writes a result report even when one or more
predictions fail and now returns a non-zero CLI exit status for partial failure.
A passing contract test with an injected adapter is labeled `injected-adapter`,
never as a verified real model execution.

A full real-model gate must additionally capture the actual installed ADMET-AI
package version, model weight revision, task documentation, endpoint units and
direction, at least ten distinct valid SMILES, full success coverage, and bounded
wall-clock/resource usage. This repository's ordinary CI does **not** meet those
requirements; no claim of toxicity validation can be made from its fixture tests.
