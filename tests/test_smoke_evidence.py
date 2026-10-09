import pytest
from amo.smoke_evidence import validate_smoke_evidence


def valid_report():
    return {
        "source": "live-admet-ai", "status": "ok", "successes": 2,
        "endpoint": {"name": "risk", "direction": "min", "unit": "native", "revision": "v1"},
        "calls": [
            {"smiles": "CCO", "status": "ok", "endpoint": "risk",
             "model_revision": "v1", "value": 0.1, "cost_units": 1},
            {"smiles": "CCN", "status": "ok", "endpoint": "risk",
             "model_revision": "v1", "value": 0.2, "cost_units": 1},
        ],
    }


def test_valid_schema():
    evidence = validate_smoke_evidence(valid_report(), required_count=2)
    assert evidence["verified_prediction_count"] == 2
    assert evidence["scientific_validity_verified"] is False


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(source="injected-adapter"),
    lambda r: r["calls"][1].update(smiles="CCO"),
    lambda r: r["calls"][0].update(value=float("nan")),
    lambda r: r["calls"][1].update(model_revision="wrong"),
    lambda r: r.update(successes=1),
    lambda r: r["calls"][0].update(cost_units=-1),
])
def test_bad_evidence_is_rejected(mutation):
    report = valid_report()
    mutation(report)
    with pytest.raises(ValueError):
        validate_smoke_evidence(report, required_count=2)
