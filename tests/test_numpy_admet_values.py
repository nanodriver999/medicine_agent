"""Real ADMET model adapters often return NumPy scalar prediction values."""
import numpy as np
from amo.admet import ADMETAdapter, Endpoint
from amo.endpoint_inventory import inspect_prediction

def test_numpy_float32_prediction_valid():
    e=Endpoint("risk","min","native","mock")
    model=ADMETAdapter(e,predictor=lambda _:{"risk":np.float32(0.375)})
    result=model.evaluate("CCO")
    assert result["status"]=="ok"
    assert result["value"] == 0.375

def test_numpy_float64_inventory_valid():
    inventory=inspect_prediction("CCO",{"risk":np.float32(.25)})
    assert inventory["endpoints"][0]["numeric_finite"] is True
    assert inventory["endpoints"][0]["sample_value"] == .25

def test_numpy_nonfinite_rejected():
    e=Endpoint("risk","min","native","mock")
    model=ADMETAdapter(e,predictor=lambda _:{"risk":np.float32("nan")})
    result=model.evaluate("CCO")
    assert result["status"]=="failed"
    assert result["value"] is None

def test_numpy_boolean_rejected():
    e=Endpoint("risk","min","native","mock")
    model=ADMETAdapter(e,predictor=lambda _:{"risk":np.bool_(True)})
    result=model.evaluate("CCO")
    assert result["status"]=="failed"
