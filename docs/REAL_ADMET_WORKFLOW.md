# Manual verification of real ADMET-AI model inference

The **ADMET-AI real-model smoke (manual)** GitHub Actions workflow is
deliberately `workflow_dispatch` only. It never runs automatically on push
or PR and is not evidence of real inference until an actual completed run
and its job logs have been reviewed.

Before manually starting it, inspect the model's actual property keys with
`amo admet-inspect`, then independently verify the unit, optimization
direction and exact model revision using official task/model documentation.
Supply those four values as workflow inputs. The workflow installs ADMET-AI,
collects 30 public ChEMBL structures, selects 10 distinct molecules and
checks that all ten predictions return finite numeric scores with full
coverage and nonzero failure exit.

The workflow uploads model outputs and installed package versions as short-
retention artifacts for reproducibility. Its environment may fail because of
model downloads, memory, runtime or incompatible package requirements.
The job has a 30-minute wall-clock timeout but the default prediction adapter
is in-process; it does not enforce an additional per-compound deadline.
A successful smoke establishes API/inference execution, **not** model
accuracy, calibrated toxicity probabilities, clinical safety, or genuine
lead optimization. Avoid manually triggering this workflow before the
required scientific endpoint metadata is confirmed.
