# Computational descriptors and constraints

- RDKit QED: unitless, maximize, not experimental activity.
- RDKit molecular weight: g/mol, configurable range.
- RDKit Crippen cLogP: predicted octanol/water partition coefficient, unitless.
- RDKit TPSA: Å², calculated descriptor.
- RDKit contributed SA_Score: synthetic accessibility heuristic, usually 1–10
  (lower is more synthetically accessible), not measured synthesis success.

The included bounds in `DEFAULT_PROPERTY_BOUNDS` are **illustrative research
filters**, not pharmacological or clinical safety thresholds. All absent/nonfinite
scores are unknown, never treated as passing.
Pareto selection requires every compared objective to be actually available.
The `sa` implementation comes from `rdkit.Contrib.SA_Score.sascorer`; record
the RDKit package version in experiment provenance and consult its bundled license.
