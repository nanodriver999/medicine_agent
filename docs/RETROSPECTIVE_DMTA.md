# Phase B: blinded ChEMBL assay retrospective replay

The `amo.retrospective` module adds a scientifically separated research path
that uses **historically measured assay values**, unlike the SHA-256 synthetic
screening oracle used by `amo compare`.

## Scope

- Filter strictly on one `assay_chembl_id`, assay type, units and '='
  uncensored relation. Positive finite measurements only.
- Reject conflicting canonical-structure duplicates rather than averaging
  across unknown experimental replicates.
- Scaffold grouping (Murcko) prevents exact scaffold overlap between train
  and holdout partitions. Larger-scale chemical series leakage still needs review.
- Selectors receive an unlabeled pool (SMILES, molecule ID, computed properties)
  with no historical activity labels. The `HiddenAssay.reveal` operation charges
  a fixed budget and returns the selected molecule's **historical** observation.
- pActivity conversion from nM assumes the assay is a molar concentration
  whose activity interpretation makes -log10(M) appropriate. Endpoint biological
  semantics should be reviewed for each chosen study.

This module supplies a deterministic API and tests, **not** a benchmark result
for a selected biological target. ChEMBL per-assay curation, target selection,
label access controls, decision trace, scaffold leakage audits, and real adaptive
acquisition policy still require scientific evaluation.

Never call replayed measurements newly synthesized or experimentally verified
in this project.
