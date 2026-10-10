from amo.admet import Endpoint, ADMETAdapter
from amo.admet_smoke import run_smoke


def test_one_retry_is_budgeted_before_prediction():
    endpoint=Endpoint("risk","min","unit","test",cost_units=1)
    counter={"calls":0}
    def predictor(smiles):
        counter["calls"]+=1
        if counter["calls"] % 2:
            raise TimeoutError("transient")
        return {"risk":0.25}
    adapter=ADMETAdapter(endpoint,predictor=predictor,max_attempts=2)
    rows=[{"molecule_id":"first","smiles":"CCO"},
          {"molecule_id":"second","smiles":"CCN"}]
    report=run_smoke(rows,endpoint,max_count=2,adapter=adapter)
    assert report["status"]=="ok"
    assert report["successes"]==2
    assert report["budget"]["used_cost_units"]==4
    assert report["budget"]["max_cost_units"]==4
    assert report["maximum_reserved_cost_per_call"]==2
    assert all(x["attempts"]==2 and x["cost_units"]==2 for x in report["calls"])


def test_retry_exhaustion_charged_but_never_mislabeled_success():
    ep=Endpoint("risk","min","unit","test")
    adapter=ADMETAdapter(ep,predictor=lambda _: (_ for _ in ()).throw(TimeoutError()),
                         max_attempts=3)
    report=run_smoke([{"molecule_id":"first","smiles":"CCO"}],ep,max_count=1,adapter=adapter)
    assert report["status"]=="partial_failure"
    assert report["successes"]==0
    assert report["budget"]["used_cost_units"]==3
    assert report["calls"][0]["attempts"]==3
