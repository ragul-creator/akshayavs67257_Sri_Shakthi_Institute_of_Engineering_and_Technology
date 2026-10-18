from pathlib import Path
import pandas as pd
from data_generation.generate_patients import generate_patients
from data_generation.generate_wearables import generate_wearables
from data_generation.generate_events import derive_events_and_labels
from ml.preprocessing import build_features
from ml.train import split_patients

def test_patient_generation_reproducible():
    pd.testing.assert_frame_equal(generate_patients(8,42),generate_patients(8,42))

def test_event_labels_are_binary():
    p=generate_patients(6,42); w=generate_wearables(p,1,43)
    labeled,events=derive_events_and_labels(w)
    assert set(labeled.target_60m.unique()).issubset({0,1}) and len(events)>0

def test_patient_split_is_disjoint():
    root=Path(__file__).resolve().parents[1]
    f=build_features(pd.read_csv(root/"data"/"sample_patients.csv"),
                     pd.read_csv(root/"data"/"sample_wearables.csv",parse_dates=["timestamp"]))
    tr,va,te=split_patients(f)
    assert not (tr&va or tr&te or va&te)

def test_scenario_does_not_mutate_twin():
    from twin_engine.state_manager import TwinEngine
    e=TwinEngine(); pid=e.patient_ids()[0]; before=e.twin(pid)
    e.run_scenario(pid,"return_toward_baseline"); after=e.twin(pid)
    assert before["current_state"]==after["current_state"]


def test_feature_schema_excludes_future_and_event_fields():
    from ml.preprocessing import feature_groups
    forbidden={"target_60m","event_onset","event_active","_sim_episode"}
    features=set()
    for group in feature_groups().values():
        features.update(group)
    assert forbidden.isdisjoint(features)


def test_simulation_reset_restores_warmup_cursor():
    from twin_engine.state_manager import TwinEngine
    e=TwinEngine(); pid=e.patient_ids()[0]
    start=e.reset(pid)["simulation"]["cursor"]
    e.step(pid,3)
    assert e.twin(pid)["simulation"]["cursor"]>start
    assert e.reset(pid)["simulation"]["cursor"]==start
