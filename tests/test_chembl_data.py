import csv
import hashlib
import json
from amo.chembl_data import parse_page, fetch_pool, write_pool


def test_dedup_and_provenance(tmp_path):
    calls = []
    def fake(url):
        calls.append(url)
        return {"molecules": [
            {"molecule_chembl_id": "CHEMBL1",
             "molecule_structures": {"canonical_smiles": "OCC"}},
            {"molecule_chembl_id": "CHEMBL2",
             "molecule_structures": {"canonical_smiles": "CCO"}},
            {"molecule_chembl_id": "CHEMBL3",
             "molecule_structures": {"canonical_smiles": "CCN"}},
            {"molecule_chembl_id": "CHEMBL4", "molecule_structures": None}]}
    rows, meta = fetch_pool(2, fetch_json=fake)
    assert len(rows) == 2
    assert len(calls) == 1
    assert "order_by=molecule_chembl_id" in calls[0]
    path = tmp_path / "pool.csv"
    manifest = write_pool(rows, meta, path)
    assert manifest["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert path.with_suffix(".manifest.json").exists()
    with path.open(newline="") as fp:
        assert len(list(csv.DictReader(fp))) == 2


def test_unexpected_payload():
    import pytest
    with pytest.raises(ValueError):
        parse_page([])
    with pytest.raises(ValueError):
        fetch_pool(0, fetch_json=lambda _: {})
