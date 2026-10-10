import pytest
from amo.live_budget_config import parse_live_llm_budget


def values():
    return {"LLM_INPUT_UNITS_PER_MILLION":"1",
            "LLM_OUTPUT_UNITS_PER_MILLION":"2",
            "LLM_PRICING_CURRENCY":"USD",
            "LLM_MAX_ROUND_CURRENCY_COST":"0.25",
            "LLM_CURRENCY_BUDGET":"1.0"}


def test_live_cost_config():
    price,budget,limit=parse_live_llm_budget(values())
    assert price.output_units_per_million==2
    assert budget.currency=="USD"
    assert limit==.25


def test_missing_configuration_fails_closed():
    for key in values():
        setting=values()
        setting.pop(key)
        with pytest.raises(ValueError):
            parse_live_llm_budget(setting)


@pytest.mark.parametrize("round_cost", ["0","2","-1","nan"])
def test_invalid_ceiling(round_cost):
    setting=values()
    setting["LLM_MAX_ROUND_CURRENCY_COST"]=round_cost
    with pytest.raises(ValueError):
        parse_live_llm_budget(setting)
