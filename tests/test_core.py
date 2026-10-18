from pathlib import Path
import pandas as pd

from data_generation.generate_patients import generate_patients
from data_generation.generate_wearables import generate_wearables
from data_generation.generate_events import derive_events_and_labels
from ml.preprocessing import build_features, feature_groups, FORBIDDEN_MODEL_FIELDS
from ml.train import split_patients

ROOT = Path(__file__).resolve().parents[1]

def test_patient_generation_reproducible():
    pd.testing.assert_frame_equal(generate_patients(8, 42), generate_patients(8, 42))

def test_latent_physiology_generation_reproducible():
    patients = generate_patients(4, 42)
    w1, l1 = generate_wearables(patients, 1, 43, return_latent=True)
    w2, l2 = generate_wearables(patients, 1, 43, return_latent=True)
    pd.testing.assert_frame_equal(w1, w2)
    pd.testing.assert_frame_equal(l1, l2)

def test_hidden_state_is_separate_from_observations():
    patients = generate_patients(3, 42)
    wearables, latent = generate_wearables(patients, 1, 43, return_latent=True)
    assert "latent_deterioration" in latent.columns
    assert not any(col.startswith("latent_") for col in wearables.columns)

def test_event_labels_come_from_aligned_latent_stream():
    patients = generate_patients(6, 42)
    wearables, latent = generate_wearables(patients, 2, 43, return_latent=True)
    labeled, events = derive_events_and_labels(wearables, latent)
    assert set(labeled.target_60m.unique()).issubset({0, 1})
    assert len(events) > 0
    assert "latent_onset_threshold" in events.columns

def test_patient_split_is_disjoint():
    patients = pd.read_csv(ROOT/"data"/"sample_patients.csv")
    wearables = pd.read_csv(ROOT/"data"/"sample_wearables.csv", parse_dates=["timestamp"])
    frame = build_features(patients, wearables)
    train, val, test = split_patients(frame)
    assert not (train & val or train & test or val & test)

def test_feature_schema_excludes_latent_and_future_fields():
    model_features = set()
    for group in feature_groups().values():
        model_features.update(group)
    assert FORBIDDEN_MODEL_FIELDS.isdisjoint(model_features)
    schema = (ROOT/"models"/"feature_schema.json").read_text()
    for forbidden in FORBIDDEN_MODEL_FIELDS:
        if forbidden.startswith("latent_"):
            assert f'"{forbidden}"' not in schema.split('"features":',1)[1].split('"feature_groups":',1)[0]

def test_scenario_is_trajectory_and_does_not_mutate_twin():
    from twin_engine.state_manager import TwinEngine
    engine = TwinEngine()
    patient_id = engine.patient_ids()[0]
    before = engine.twin(patient_id)
    result = engine.run_scenario(patient_id, "recovery")
    after = engine.twin(patient_id)
    assert len(result["trajectory"]) == 12
    assert result["hypothetical"] is True
    assert before["current_state"] == after["current_state"]
    assert before["simulation"]["cursor"] == after["simulation"]["cursor"]

def test_state_estimate_does_not_expose_hidden_simulator_state():
    from twin_engine.state_manager import TwinEngine
    engine = TwinEngine()
    twin = engine.twin(engine.patient_ids()[0])
    state = twin["estimated_state"]
    assert "physiologic_strain" in state
    assert not any(key.startswith("latent_") for key in state)

def test_simulation_reset_restores_warmup_cursor():
    from twin_engine.state_manager import TwinEngine
    engine = TwinEngine()
    patient_id = engine.patient_ids()[0]
    start = engine.reset(patient_id)["simulation"]["cursor"]
    engine.step(patient_id, 3)
    assert engine.twin(patient_id)["simulation"]["cursor"] > start
    assert engine.reset(patient_id)["simulation"]["cursor"] == start
