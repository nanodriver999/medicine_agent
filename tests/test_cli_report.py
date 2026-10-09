import csv
import json
import subprocess
import sys
from pathlib import Path
from amo.ui import load_report


def test_compare_cli_and_readonly_report(tmp_path):
    root = Path(__file__).resolve().parents[1]
    data = root / "data" / "fixtures" / "smiles.csv"
    dest = tmp_path / "compare"
    command = [sys.executable, "-m", "amo.cli", "compare", "--input", str(data),
               "--out", str(dest), "--budget", "3",
               "--seeds", "42", "43", "44"]
    process = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(process.stdout)["runs"] == 9
    report = load_report(dest)
    assert len(report["runs"]) == 9
    assert all(row["mode"] == "offline-fixture" for row in report["runs"])
    assert len({row["cost_units"] for row in report["runs"]}) == 1
    manifest = json.loads((dest / "manifest.json").read_text())
    assert len(manifest["input_sha256"]) == 64
    with (dest / "comparison.csv").open(newline="") as fp:
        assert len(list(csv.DictReader(fp))) == 9
    assert process.returncode == 0


def test_ui_loader_rejects_malformed_report(tmp_path):
    (tmp_path / "comparison.json").write_text('{"runs": []}')
    import pytest
    with pytest.raises(ValueError):
        load_report(tmp_path)
