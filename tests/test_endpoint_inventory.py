import json
import pytest
from amo.endpoint_inventory import inspect_prediction, save_inventory


def test_inventory_records_fields_not_semantics(tmp_path):
    result = inspect_prediction("OCC", {"BBB": 0.9, "hERG": 0.2})
    assert result["probe_smiles"] == "CCO"
    assert [x["name"] for x in result["endpoints"]] == ["BBB", "hERG"]
    assert result["direction"] == "UNVERIFIED"
    assert result["unit"] == "UNVERIFIED"
    destination = tmp_path / "inventory.json"
    save_inventory(result, destination)
    assert len(json.loads(destination.read_text())["endpoints"]) == 2


def test_nonfinite_and_invalid_never_interpreted_as_risk():
    result = inspect_prediction("CCO", {"unknown": float("nan"), "other": "safe"})
    assert all(not x["numeric_finite"] and x["sample_value"] is None
               for x in result["endpoints"])
    for raw in ({}, [], {"bad": None} if False else {}):
        with pytest.raises(ValueError):
            inspect_prediction("CCO", raw)
    with pytest.raises(ValueError):
        inspect_prediction("not-a-smiles", {"x": 1})
