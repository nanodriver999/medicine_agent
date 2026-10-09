import pytest
from amo.txgemma import (TxTask, build_tdc_prompt, parse_classification,
                        parse_regression, predict)

TEMPLATE = "Question: Given a drug SMILES string predict (A) no (B) yes. Drug SMILES: {Drug SMILES}\nAnswer:"


@pytest.mark.parametrize("input_value, expected", [
    ("A", "A"), ("(A)", "A"), (" b ", "B"), (" (b) ", "B")
])
def test_exact_labels(input_value, expected):
    assert parse_classification(input_value)["value"] == expected


@pytest.mark.parametrize("bad", ["A and B", "BBB", "B crosses BBB", "Answer: A",
                                  "yes", "0.9", "A. B", "", "A.", " A because"])
def test_ambiguous_classification_is_rejected(bad):
    assert parse_classification(bad)["status"] == "parse_error"


def test_regression_strict_numeric():
    assert parse_regression(" -1.2e-2 ")["value"] == -0.012
    for bad in ["NaN", "inf", "0.1 (approx)", "value: 1", "1,2", ""]:
        assert parse_regression(bad)["status"] == "parse_error"


def test_prompt_and_predict():
    prompt = build_tdc_prompt(TEMPLATE, "OCC")
    assert "CCO" in prompt
    task = TxTask("BBB_Martins", TEMPLATE, "classification", "test-only-revision")
    result = predict("CCO", task, lambda p: "(B)")
    assert result["status"] == "ok"
    assert result["value"] == "B"
    assert result["calibrated_probability"] is False
    assert predict("CCO", task, lambda p: "A and B")["status"] == "parse_error"
    with pytest.raises(ValueError):
        build_tdc_prompt("missing placeholder", "CCO")
