import math
import pytest
from amo.retrospective import (curate_assay, scaffold_group, split_scaffolds,
                               Observation, HiddenAssay, replay)


def _row(smi, compound, value, relation="=", assay="CHEMBL_ASSAY1", unit="nM"):
    return {"canonical_smiles": smi, "molecule_chembl_id": compound,
            "assay_chembl_id": assay, "standard_type": "IC50",
            "standard_units": unit, "standard_relation": relation,
            "standard_value": str(value)}


def test_assay_curation_rejects_wrong_assay_censored_and_conflicts():
    source = [
        _row("CCO", "CHEMBL1", 50),
        _row("CCO", "CHEMBL1", 100),
        _row("CCN", "CHEMBL2", 20),
        _row("c1ccccc1", "CHEMBL3", 2, relation="<"),
        _row("CCCC", "CHEMBL4", 80, assay="OTHER"),
        _row("CC(C)O", "CHEMBL5", -10),
        _row("CCF", "CHEMBL6", float("nan")),
    ]
    obs = curate_assay(source, assay_id="CHEMBL_ASSAY1")
    assert len(obs) == 1
    assert obs[0].molecule_id == "CHEMBL2"
    assert obs[0].value == 20


def test_blinded_reveal_and_budget():
    obs = [Observation("a", "CCO", 10, "assay", "IC50", "nM"),
           Observation("b", "c1ccccc1", 100, "assay", "IC50", "nM")]
    hidden = HiddenAssay(obs, max_evaluations=1)
    view = hidden.visible_pool()
    assert all("value" not in row and "p_activity" not in row
               and "observed_value" not in row for row in view)
    result = hidden.reveal("a")
    assert math.isclose(result["p_activity"], 8.0)
    assert result["status"] == "measured_historical"
    assert hidden.reveal("a")["cost_units"] == 0
    with pytest.raises(ValueError):
        hidden.reveal("b")
    with pytest.raises(ValueError):
        hidden.reveal("bad")
    answer = replay(obs, budget=1, selector=lambda unlabeled:
                    [unlabeled[0]["molecule_id"]])
    assert len(answer["observations"]) == 1
    assert answer["consumed_cost_units"] == 1


def test_scaffold_split_no_leakage():
    obs = [Observation(f"m{i}", s, 10, "assay", "IC50", "nM")
           for i, s in enumerate(["c1ccccc1", "Cc1ccccc1", "c1ccncc1", "CCO", "CCN"])]
    training, holdout = split_scaffolds(obs, train_fraction=0.6)
    assert {scaffold_group(x.smiles) for x in training}.isdisjoint(
        {scaffold_group(x.smiles) for x in holdout})
    assert {x.molecule_id for x in training + holdout} == {x.molecule_id for x in obs}
