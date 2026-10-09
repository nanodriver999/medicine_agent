"""Public ChEMBL molecule-pool acquisition with immutable source metadata.

Not a target-activity dataset: molecules are sampled from the public registry,
and no potency/bioactivity labels are inferred or manufactured.
"""
from __future__ import annotations
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from .core import prepare

API = "https://www.ebi.ac.uk/chembl/api/data/molecule.json"


def parse_page(raw: dict) -> list[dict]:
    if not isinstance(raw, dict) or not isinstance(raw.get("molecules"), list):
        raise ValueError("unexpected ChEMBL page shape")
    rows = []
    for molecule in raw["molecules"]:
        if not isinstance(molecule, dict):
            continue
        structures = molecule.get("molecule_structures") or {}
        smiles = structures.get("canonical_smiles") if isinstance(structures, dict) else None
        chembl_id = molecule.get("molecule_chembl_id")
        if isinstance(smiles, str) and isinstance(chembl_id, str) and chembl_id.startswith("CHEMBL"):
            rows.append({"molecule_id": chembl_id, "smiles": smiles})
    return rows


def fetch_pool(target_count: int, *, page_size: int = 250, max_pages: int = 30,
               fetch_json=None) -> tuple[list[dict], dict]:
    if target_count < 1 or page_size < 1 or page_size > 1000 or max_pages < 1:
        raise ValueError("invalid acquisition limits")
    if fetch_json is None:
        def fetch_json(url):
            with urlopen(url, timeout=30) as response:
                return json.load(response)
    rows, seen, urls = [], set(), []
    for page in range(max_pages):
        query = urlencode({"limit": page_size, "offset": page * page_size,
                           "order_by": "molecule_chembl_id"})
        url = API + "?" + query
        urls.append(url)
        page_data = fetch_json(url)
        for row in prepare(parse_page(page_data)):
            if row["smiles"] not in seen:
                seen.add(row["smiles"])
                rows.append(row)
            if len(rows) >= target_count:
                break
        if len(rows) >= target_count or not page_data["molecules"]:
            break
    metadata = {"source": API, "query_urls": urls,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "selected": len(rows),
                "sampling": "ordered public molecule registry subset; not random or representative",
                "activity_labels": "none",
                "license": "consult ChEMBL official source terms before redistributing"}
    return rows, metadata


def write_pool(rows: list[dict], metadata: dict, output: str | Path) -> dict:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["molecule_id", "smiles"])
        writer.writeheader()
        writer.writerows(rows)
    manifest = {**metadata, "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "output_file": output.name}
    output.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
