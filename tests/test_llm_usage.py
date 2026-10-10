import pytest
from amo.llm_usage import LLMUsageLedger, Pricing

def test_usage_cost_and_sum():
    l=LLMUsageLedger(Pricing(2,4),"example-revision")
    l.add(input_tokens=100000,output_tokens=50000,source="provider_usage")
    l.add(input_tokens=0,output_tokens=25000,source="provider_usage")
    assert l.summary()["llm_cost_units"] == pytest.approx(0.5)
    assert l.summary()["input_tokens"] == 100000
    assert l.summary()["usage_status"] == "verified"

def test_missing_usage_cannot_be_claimed_verified():
    assert LLMUsageLedger(Pricing(1,1),"v1").summary()["usage_status"] == "missing_provider_usage"

@pytest.mark.parametrize("input_tokens,output_tokens,source",[
    (-1,0,"provider_usage"),(1.5,0,"provider_usage"),
    (True,0,"provider_usage"),(0,0,"estimated")])
def test_unverified_usage_rejected(input_tokens,output_tokens,source):
    ledger=LLMUsageLedger(Pricing(1,1),"v1")
    with pytest.raises(ValueError):
        ledger.add(input_tokens=input_tokens,output_tokens=output_tokens,source=source)

def test_invalid_pricing_rejected():
    with pytest.raises(ValueError):
        Pricing(-1,1)
