from types import SimpleNamespace
from amo.strands_usage import extract_strands_usage
from amo.llm_usage import LLMUsageLedger, Pricing

def result(usage):
    return SimpleNamespace(metrics=SimpleNamespace(accumulated_usage=usage))

def test_strands_result_and_ledger():
    tokens = extract_strands_usage(result({"inputTokens": 100, "outputTokens": 50, "totalTokens": 150}))
    assert tokens["status"] == "ok"
    ledger = LLMUsageLedger(Pricing(1, 2), "test-model")
    ledger.add(input_tokens=tokens["input_tokens"], output_tokens=tokens["output_tokens"], source="provider_usage")
    assert ledger.summary()["llm_cost_units"] == 0.0002

def test_missing_or_inconsistent_usage():
    assert extract_strands_usage(SimpleNamespace())["status"] == "missing_provider_usage"
    for bad in ({"inputTokens": 1, "outputTokens": -1},
                {"inputTokens": True, "outputTokens": 2},
                {"inputTokens": 3, "outputTokens": 2, "totalTokens": 9}):
        assert extract_strands_usage(result(bad))["status"] == "invalid_provider_usage"
