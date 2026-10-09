from amo.agent_live import live_agent_run, export_live_agent_run
from amo.admet import Endpoint, ADMETAdapter
import json


def test_mock_driver_uses_real_validation_path(tmp_path):
    endpoint = Endpoint("fake_toxicity", "min", "unitless", "fake-v1")
    adapter = ADMETAdapter(endpoint, predictor=lambda smi: {"fake_toxicity": 0.2})
    def driver(session):
        assert session.evaluate("bad", "admet_ai", "fake_toxicity")["status"] == "rejected"
        available = sorted(session.molecules)
        assert available
        assert session.evaluate(available[0], "admet_ai", "fake_toxicity")["status"] == "ok"
        assert session.evaluate(available[0], "admet_ai", "fake_toxicity")["status"] == "rejected"
        return {"status": "ok"}
    report = live_agent_run([{"molecule_id": "m1", "smiles": "CCO"}], endpoint,
                            budget_units=1, adapter=adapter, driver=driver)
    assert report["status"] == "ok"
    assert len(report["evaluated"]) == 1
    assert report["evaluated"][0]["fake_toxicity"] == 0.2
    assert report["budget"]["tool_calls"] == 1
    export_live_agent_run(report, tmp_path)
    assert json.loads((tmp_path / "agent_run.json").read_text())["mode"] == "live-agent"


def test_llm_driver_bad_action_cannot_spend_budget():
    endpoint = Endpoint("task", "min", "unitless", "fake-v1")
    adapter = ADMETAdapter(endpoint, predictor=lambda _: {"task": 0.5})
    def driver(session):
        response = session.evaluate("m1", "subprocess", "exec")
        assert response["status"] == "rejected"
        return {"status": "failed"}
    report = live_agent_run([{"molecule_id": "m1", "smiles": "CCO"}],
                            endpoint, budget_units=1, adapter=adapter, driver=driver)
    assert report["budget"]["used_cost_units"] == 0
    assert report["evaluated"] == []
