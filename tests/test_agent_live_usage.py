from amo.agent_live import live_agent_run
from amo.admet import ADMETAdapter, Endpoint

def test_live_report_propagates_verified_cost_and_usage():
    endpoint=Endpoint("risk","min","native","fake-v1")
    adapter=ADMETAdapter(endpoint,predictor=lambda _: {"risk":0.5})
    def driver(session):
        item=next(iter(session.molecules))
        session.evaluate(item,"admet_ai","risk")
        return {"status":"ok",
                "token_usage":{"status":"ok","input_tokens":40,"output_tokens":20},
                "llm_cost":{"usage_status":"verified","llm_cost_units":0.00008}}
    result=live_agent_run([{"molecule_id":"m1","smiles":"CCO"}],
                          endpoint,adapter=adapter,driver=driver,budget_units=1)
    assert result["token_usage"]["input_tokens"] == 40
    assert result["llm_cost"]["usage_status"] == "verified"

def test_missing_token_usage_remains_explicit():
    endpoint=Endpoint("risk","min","native","fake-v1")
    adapter=ADMETAdapter(endpoint,predictor=lambda _: {"risk":0.5})
    result=live_agent_run([{"molecule_id":"m1","smiles":"CCO"}],endpoint,
                          adapter=adapter,driver=lambda s: {"status":"ok"},budget_units=1)
    assert result["llm_cost"]["usage_status"] == "missing_pricing_configuration"
    assert result["token_usage"]["status"] == "missing_provider_usage"
