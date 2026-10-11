from amo.evaluation import run_comparison


def test_synthetic_comparison_has_paired_intervals():
    rows=[{"molecule_id":f"m{i}","smiles":s} for i,s in enumerate(
        ["CCO","CCN","CCC","CCCl","CCBr","CC(=O)O"])]
    result=run_comparison(rows,seeds=(42,43,44),policies=("fixed","rules","agent"),budget=3)
    assert len(result["paired_intervals"])==3
    for pair in result["paired_intervals"]:
        assert pair["policy_a"]!=pair["policy_b"]
        assert pair.get("paired_seeds")==3
        assert pair["scope"]=="descriptive interval across the tested seeds only"
    assert "Synthetic oracle" in result["warning"]


def test_two_seed_comparison_does_not_fabricate_interval():
    rows=[{"molecule_id":"m1","smiles":"CCO"}]
    result=run_comparison(rows,seeds=(42,43),policies=("fixed","rules"),budget=1)
    assert result["paired_intervals"]==[]
