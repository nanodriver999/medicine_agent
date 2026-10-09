# Public ChEMBL pool integration workflow

The `ChEMBL public pool smoke` GitHub Actions workflow is triggered once
when its workflow file is added, and can later be dispatched manually.
It uses the public ChEMBL API to retrieve 120 molecule structures, validates at
least 100 distinct RDKit-canonical SMILES, records source URLs and SHA256, and
runs all three **synthetic offline fixture policies** across three seeds.

GitHub Actions publishes short-lived candidate-pool and output artifacts.
The downloaded data are not silently committed to Git; preserve artifacts and
checksums for future reproducibility when source/license terms allow it.

This validates public-data retrieval and software workflow only. Even if all
runs succeed, the synthetic oracle does not represent biological activity, and
the `agent` fixture policy is not a live LLM.
