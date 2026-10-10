"""Exercise live_agent_run default Strands path with a fake SDK, no API calls."""
import sys
import types
from types import SimpleNamespace
import pytest
from amo.admet import ADMETAdapter, Endpoint
from amo.agent_live import live_agent_run

def install_fake_strands(monkeypatch, *, missing_usage=False):
    package=types.ModuleType("strands")
    package.__path__=[]
    models=types.ModuleType("strands.models")
    models.__path__=[]
    openai=types.ModuleType("strands.models.openai")
    class OpenAIModel:
        def __init__(self, **kwargs):
            self.kwargs=kwargs
    class Agent:
        def __init__(self, *, model, tools, system_prompt):
            self.tools=tools
            self.model=model
        def __call__(self, prompt):
            assert "m1" in prompt
            result=self.tools[0]("m1","admet_ai","risk")
            assert result["status"] == "ok"
            usage=None if missing_usage else {
                "inputTokens":100,"outputTokens":50,"totalTokens":150}
            return SimpleNamespace(metrics=SimpleNamespace(accumulated_usage=usage))
    package.Agent=Agent
    package.tool=lambda fn:fn
    openai.OpenAIModel=OpenAIModel
    monkeypatch.setitem(sys.modules,"strands",package)
    monkeypatch.setitem(sys.modules,"strands.models",models)
    monkeypatch.setitem(sys.modules,"strands.models.openai",openai)

def configure(monkeypatch):
    setting={
      "LLM_MODEL":"test-model",
      "LLM_API_KEY":"test-key",
      "LLM_INPUT_UNITS_PER_MILLION":"1",
      "LLM_OUTPUT_UNITS_PER_MILLION":"2",
      "LLM_PRICING_CURRENCY":"USD",
      "LLM_MAX_ROUND_CURRENCY_COST":"0.01",
      "LLM_CURRENCY_BUDGET":"1",
      "EVALUATION_CURRENCY_PER_COST_UNIT":"0.5",
    }
    for k,v in setting.items():
        monkeypatch.setenv(k,v)

def run(monkeypatch, *, missing_usage=False):
    configure(monkeypatch)
    install_fake_strands(monkeypatch,missing_usage=missing_usage)
    endpoint=Endpoint("risk","min","native","mock-rev")
    adapter=ADMETAdapter(endpoint,predictor=lambda _:{"risk":0.1})
    return live_agent_run([{"molecule_id":"m1","smiles":"CCO"}],
                          endpoint,budget_units=1,adapter=adapter)

def test_default_strands_driver_with_cost_and_model_tool(monkeypatch):
    report=run(monkeypatch)
    assert report["status"] == "ok"
    assert len(report["evaluated"]) == 1
    assert report["token_usage"]["input_tokens"] == 100
    assert report["llm_cost"]["usage_status"] == "verified"
    assert report["llm_currency_budget"]["spent"] == pytest.approx(0.0002)
    assert report["total_cost"]["total_cost_currency"] == pytest.approx(0.5002)

def test_default_strands_missing_usage_not_claimed_success(monkeypatch):
    report=run(monkeypatch,missing_usage=True)
    assert report["status"] == "incomplete_usage"
    assert report["llm_cost"]["usage_status"] == "missing_provider_usage"
    assert report["llm_currency_budget"]["spent"] == pytest.approx(0.01)
    assert report["total_cost"]["status"] == "incomplete"
