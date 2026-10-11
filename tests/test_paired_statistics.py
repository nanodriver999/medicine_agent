import pytest
from amo.paired_statistics import paired_bootstrap

def data():
    return [{"policy":p, "seed":s, "score":v}
            for p, values in (("fixed",[1,2,3,4]),("rules",[2,3,4,5]))
            for s, v in zip((10,11,12,13),values)]

def test_paired_difference_and_determinism():
    a=paired_bootstrap(data(),metric="score",policy_a="rules",policy_b="fixed",
                       draws=200,seed=7)
    b=paired_bootstrap(list(reversed(data())),metric="score",
                       policy_a="rules",policy_b="fixed",draws=200,seed=7)
    assert a==b
    assert a["mean_difference"]==1
    assert a["interval_low"]==a["interval_high"]==1
    assert a["paired_seeds"]==4

def test_missing_or_unpaired_seed_fails():
    d=data()
    d.pop()
    with pytest.raises(ValueError,match="unpaired"):
        paired_bootstrap(d,metric="score",policy_a="rules",policy_b="fixed")
    d=data()
    d[0]["score"]=None
    with pytest.raises(ValueError,match="missing"):
        paired_bootstrap(d,metric="score",policy_a="rules",policy_b="fixed")

def test_duplicates_and_small_n_rejected():
    with pytest.raises(ValueError,match="unique"):
        paired_bootstrap(data()+[data()[0]],metric="score",
                         policy_a="rules",policy_b="fixed")
    small=[r for r in data() if r["seed"] in (10,11)]
    with pytest.raises(ValueError,match="three"):
        paired_bootstrap(small,metric="score",policy_a="rules",policy_b="fixed")

@pytest.mark.parametrize("bad", [float("nan"),float("inf"),True,"fake"])
def test_bad_observations_rejected(bad):
    d=data()
    d[0]["score"]=bad
    with pytest.raises(ValueError):
        paired_bootstrap(d,metric="score",policy_a="rules",policy_b="fixed")
