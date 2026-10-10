from pathlib import Path


def test_evidence_artifacts_are_inside_workspace():
    workflow = (Path(__file__).resolve().parents[1] /
                ".github/workflows/admet-real-smoke.yml").read_text()
    assert "outputs/admet-installed-versions.txt" in workflow
    assert "outputs/runtime.json" in workflow
    assert "outputs/chembl_smoke.sha256" in workflow
    assert "data/processed/chembl_smoke.csv" in workflow
    assert "/tmp/admet-installed-versions.txt" not in workflow
    assert "not-installed-or-injected" in workflow
