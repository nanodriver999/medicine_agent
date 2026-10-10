from amo.agent_live import live_agent_run
from amo.admet import Endpoint, ADMETAdapter
import pytest

def test_missing_total_cost_keeps_incomplete_state(monkeypatch):
    monkeypatch.delenv("LLM_PRICING_CURRENCY", raising=False)
    monkeypatch.delenv("EVALUATION_CURRENCY_PER_COST_UNIT", raising=False)
    ep = Endpoint("risk", "min", "model_native", "fake-v1")
    adapter = ADMETAdapter(ep, predictor=lambda _: {"risk": .2})
    report = live_agent_run([{"molecule_id":"a","smiles":"CCO"}],ep,
                            adapter=adapter,driver=lambda session: {"status":"ok"},budget_units=1)
    assert report["total_cost"]["status"] == "incomplete"
    assert report["total_cost"]["total_cost_currency"] is None

def test_explicit_conversion_reconciles_injected_usage(monkeypatch):
    monkeypatch.setenv("LLM_PRICING_CURRENCY","USD")
    monkeypatch.setenv("EVALUATION_CURRENCY_PER_COST_UNIT","0.5")
    ep = Endpoint("risk", "min", "model_native", "fake-v1")
    adapter = ADMETAdapter(ep, predictor=lambda _: {"risk": .2})
    def driver(session):
        molecule_id = next(iter(session.molecules))
        session.evaluate(molecule_id, "admet_ai", "risk")
        return {"status":"ok", "llm_cost":{"usage_status":"verified","llm_cost_units":0.1}}
    report=live_agent_run([{"molecule_id":"a","smiles":"CCO"}],ep,
                          adapter=adapter,driver=driver,budget_units=1)
    assert report["total_cost"]["status"] == "complete"
    assert report["total_cost"]["total_cost_currency"] == pytest.approx(0.6)
