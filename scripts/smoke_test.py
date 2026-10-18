from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from twin_engine.state_manager import TwinEngine

def main():
    engine = TwinEngine()
    patient_id = engine.patient_ids()[0]
    start = engine.reset(patient_id)
    stepped = engine.step(patient_id, 1)
    scenario = engine.run_scenario(patient_id, "recovery")

    assert stepped["simulation"]["cursor"] > start["simulation"]["cursor"]
    assert 0 <= stepped["forecast"]["event_probability"] <= 1
    assert "physiologic_strain" in stepped["estimated_state"]
    assert len(scenario["trajectory"]) == 12

    print({
        "status": "ok",
        "patient_id": patient_id,
        "cursor": stepped["simulation"]["cursor"],
        "probability": stepped["forecast"]["event_probability"],
        "state_confidence": stepped["estimated_state"]["confidence"],
        "scenario_end_probability": scenario["end_probability"],
        "model_version": stepped["forecast"]["model_version"],
    })

if __name__ == "__main__":
    main()
