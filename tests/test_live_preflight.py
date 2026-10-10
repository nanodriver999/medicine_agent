import pytest
from amo.admet import Endpoint, ADMETAdapter
from amo.agent_live import live_agent_run


def test_budget_invalid_before_importing_strands(monkeypatch):
    for key in ("LLM_MODEL","LLM_API_KEY"):
        monkeypatch.setenv(key,"test-value")
    for key in ("LLM_INPUT_UNITS_PER_MILLION","LLM_OUTPUT_UNITS_PER_MILLION",
                "LLM_PRICING_CURRENCY","LLM_MAX_ROUND_CURRENCY_COST",
                "LLM_CURRENCY_BUDGET"):
        monkeypatch.delenv(key,raising=False)
    endpoint=Endpoint("risk","min","native","fake-revision")
    adapter=ADMETAdapter(endpoint,predictor=lambda _:{"risk":0.2})
    with pytest.raises(ValueError,match="missing verified LLM pricing"):
        live_agent_run([{"molecule_id":"m1","smiles":"CCO"}],endpoint,
                       adapter=adapter,budget_units=1)


def test_injected_driver_does_not_require_real_budget_settings(monkeypatch):
    for key in ("LLM_MODEL","LLM_API_KEY"):
        monkeypatch.delenv(key,raising=False)
    endpoint=Endpoint("risk","min","native","fake-revision")
    adapter=ADMETAdapter(endpoint,predictor=lambda _:{"risk":0.2})
    report=live_agent_run([{"molecule_id":"m1","smiles":"CCO"}],endpoint,
                          adapter=adapter,driver=lambda s:{"status":"ok"},budget_units=1)
    assert report["status"]=="ok"
    assert report["total_cost"]["status"]=="incomplete"
