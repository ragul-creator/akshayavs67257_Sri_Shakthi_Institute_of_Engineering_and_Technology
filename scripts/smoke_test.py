from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from twin_engine.state_manager import TwinEngine

def main():
    engine=TwinEngine()
    pid=engine.patient_ids()[0]
    start=engine.reset(pid)
    stepped=engine.step(pid,1)
    scenario=engine.run_scenario(pid,"return_toward_baseline")
    assert start["patient_id"]==pid
    assert stepped["simulation"]["cursor"]>start["simulation"]["cursor"]
    assert 0<=stepped["forecast"]["event_probability"]<=1
    assert scenario["hypothetical"] is True
    print({
        "status":"ok",
        "patient_id":pid,
        "cursor":stepped["simulation"]["cursor"],
        "probability":stepped["forecast"]["event_probability"],
        "scenario_probability":scenario["scenario_probability"],
        "model_version":stepped["forecast"]["model_version"],
    })

if __name__=="__main__":
    main()
