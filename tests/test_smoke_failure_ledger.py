from amo.admet import Endpoint
from amo.admet_smoke import run_smoke


class BadAdapter:
    max_attempts=2
    def __init__(self, outcome):
        self.outcome=outcome
    def evaluate(self, smiles):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def test_unexpected_exception_recorded_and_reserved():
    endpoint=Endpoint("risk","min","native","mock")
    result=run_smoke([{"smiles":"CCO"}],endpoint,max_count=1,
                     adapter=BadAdapter(RuntimeError("do not expose secret")))
    assert result["status"]=="partial_failure"
    assert result["calls"][0]["error_code"]=="RuntimeError"
    assert result["calls"][0]["cost_units"]==2
    assert result["budget"]["used_cost_units"]==2
    assert "secret" not in str(result)


def test_missing_cost_is_not_free():
    endpoint=Endpoint("risk","min","native","mock")
    result=run_smoke([{"smiles":"CCO"}],endpoint,max_count=1,
                     adapter=BadAdapter({"status":"ok","value":0.4}))
    assert result["calls"][0]["error_code"]=="UnverifiedCost"
    assert result["calls"][0]["cost_units"]==2
    assert result["successes"]==0


def test_nonfinite_and_overlimit_cost_fail_closed():
    endpoint=Endpoint("risk","min","native","mock")
    for claimed in (float("nan"),float("inf"),3,-1,True):
        result=run_smoke([{"smiles":"CCO"}],endpoint,max_count=1,
              adapter=BadAdapter({"status":"ok","value":.2,"cost_units":claimed}))
        assert result["status"]=="partial_failure"
        assert result["calls"][0]["cost_units"]==2
