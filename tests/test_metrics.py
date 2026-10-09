import math
import pytest
from amo.metrics import hypervolume_qed_risk, cost_curve


def test_hypervolume_reference_and_partial_coverage():
    rows = [{"qed": 0.2, "fixture_risk": 0.2},
            {"qed": 0.8, "fixture_risk": 0.8},
            {"qed": 0.9, "fixture_risk": None}]
    # Union of two rectangles anchored at (0,0):
    # 0.2*0.8 + (0.8-0.2)*0.2 = 0.28
    assert math.isclose(hypervolume_qed_risk(rows), 0.28, abs_tol=1e-10)
    assert hypervolume_qed_risk([{"qed": 1, "fixture_risk": None}]) == 0
    assert hypervolume_qed_risk([]) == 0
    with pytest.raises(ValueError):
        hypervolume_qed_risk([{"qed": 2, "fixture_risk": 0}])


def test_budget_curve_monotonic_coverage_and_hv():
    sequence = [{"qed": 0.2, "fixture_risk": 0.2},
                {"qed": 0.8, "fixture_risk": 0.8},
                {"qed": 0.3, "fixture_risk": 0.9}]
    curve = cost_curve(sequence, 1)
    assert [x["cost_units"] for x in curve] == [1, 2, 3]
    assert curve[0]["hypervolume_qed_risk"] <= curve[-1]["hypervolume_qed_risk"]
    assert curve[0]["best_fixture_objective"] <= curve[-1]["best_fixture_objective"]
    with pytest.raises(ValueError):
        cost_curve(sequence, -1)
