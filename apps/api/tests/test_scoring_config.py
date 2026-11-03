from services.scoring_config import DEFAULTS, apply


def test_apply_merges_partial_weights_without_mutating_defaults():
    out = apply({"priority": {"time": 0.30}, "risk": {"web": 0.30}})
    assert out["priority"]["time"] == 0.30
    assert out["priority"]["criticality"] == DEFAULTS["priority"]["criticality"]
    assert out["risk"]["web"] == 0.30
    assert set(out) == {"priority", "risk", "overlap"}
