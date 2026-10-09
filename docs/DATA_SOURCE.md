# Candidate molecule pool acquisition

The smoke fixture `data/fixtures/smiles.csv` is hand-authored and is **not** a
scientific benchmark. For a fixed pool of at least 100 externally sourced structures,
retrieve a public ChEMBL molecule subset:

```bash
python scripts/fetch_chembl_pool.py --count 120 --out data/processed/chembl_pool.csv
amo prepare --input data/processed/chembl_pool.csv --output data/processed/chembl_pool_clean.csv
amo compare --input data/processed/chembl_pool_clean.csv --budget 30 --out outputs/chembl_compare
```

The downloader uses official ChEMBL molecule JSON API with deterministic ordering,
canonicalizes/deduplicates SMILES, retains CHEMBL IDs and writes a source URL list,
timestamp, input SHA256 and provenance manifest. Confirm official license and source
terms before redistribution. Source: https://www.ebi.ac.uk/chembl/api/data/molecule

**Bias warning:** the ordered registry subset is *not* a representative random sample
of all drug-like molecules. It contains **no target assay labels** and should not be
used to claim actual lead optimization, validated ADMET improvement, or clinical safety.

The downloader is network-dependent and opt-in; offline tests use fake JSON pages,
not the real ChEMBL service. Pin an actual retrieved dataset as a release artifact
or checksum-verified file for serious multi-seed benchmarking.
