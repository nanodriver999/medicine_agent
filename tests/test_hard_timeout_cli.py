import subprocess
import sys
from pathlib import Path


def test_hard_timeout_option_exposed():
    result = subprocess.run([sys.executable, "-m", "amo.cli", "admet-smoke", "--help"],
                            capture_output=True, text=True, check=True)
    assert "--hard-timeout" in result.stdout


def test_unset_timeout_does_not_change_offline_cli(tmp_path):
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "amo.cli", "compare", "--input",
               str(root / "data/fixtures/smiles.csv"), "--budget", "1",
               "--out", str(tmp_path)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    assert (tmp_path / "comparison.json").exists()
