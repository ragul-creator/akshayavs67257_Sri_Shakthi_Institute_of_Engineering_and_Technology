from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from ml.preprocessing import build_features

SCENARIO_NAMES = ("recovery", "sustained_activity")

@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    activity_load: float
    recovery_drive: float
    label: str
    assumptions: tuple[str, ...]

SCENARIOS = {
    "recovery": ScenarioSpec(
        name="recovery",
        activity_load=0.0,
        recovery_drive=0.85,
        label="Recovery trajectory",
        assumptions=(
            "Future activity is held at rest for 60 simulated minutes.",
            "Observed HR/BP are allowed to relax toward the patient's generated baseline.",
            "HRV is allowed to recover toward an age-adjusted reference.",
        ),
    ),
    "sustained_activity": ScenarioSpec(
        name="sustained_activity",
        activity_load=0.70,
        recovery_drive=0.10,
        label="Sustained activity trajectory",
        assumptions=(
            "Moderate activity load is sustained for the first 40 simulated minutes.",
            "The trajectory uses an observation-space response model, not a treatment-effect model.",
            "Sensor quality is held adequate to isolate the scenario trajectory.",
        ),
    ),
}

RAW_COLUMNS = [
    "timestamp", "patient_id", "heart_rate_bpm", "hrv_ms",
    "systolic_bp", "diastolic_bp", "steps", "activity_state",
    "sleep_state", "sensor_quality", "missing_data_indicator",
]

def _next_observation(previous: dict, profile: dict, step: int, spec: ScenarioSpec) -> dict:
    baseline_hr = float(profile["baseline_hr"])
    baseline_sys = float(profile["historical_systolic_bp"])
    baseline_dia = float(profile["historical_diastolic_bp"])
    age_hrv = max(30.0, min(62.0, 58.0 - 0.22 * (float(profile["age"]) - 45.0)))

    if spec.name == "sustained_activity" and step >= 8:
        activity = 0.25
    else:
        activity = spec.activity_load
    recovery = spec.recovery_drive

    hr = (
        float(previous["heart_rate_bpm"])
        + 0.16 * (baseline_hr - float(previous["heart_rate_bpm"]))
        + 5.8 * activity - 2.2 * recovery
    )
    systolic = (
        float(previous["systolic_bp"])
        + 0.13 * (baseline_sys - float(previous["systolic_bp"]))
        + 4.6 * activity - 1.6 * recovery
    )
    diastolic = (
        float(previous["diastolic_bp"])
        + 0.12 * (baseline_dia - float(previous["diastolic_bp"]))
        + 2.0 * activity - 0.8 * recovery
    )
    hrv = (
        float(previous["hrv_ms"])
        + 0.15 * (age_hrv - float(previous["hrv_ms"]))
        - 2.5 * activity + 1.6 * recovery
    )
    return {
        "timestamp": pd.Timestamp(previous["timestamp"]) + pd.Timedelta(minutes=5),
        "patient_id": previous["patient_id"],
        "heart_rate_bpm": round(hr, 2),
        "hrv_ms": round(max(10.0, hrv), 2),
        "systolic_bp": round(systolic, 2),
        "diastolic_bp": round(diastolic, 2),
        "steps": int(4 + 45 * activity),
        "activity_state": "active" if activity >= 0.5 else "rest",
        "sleep_state": 0,
        "sensor_quality": 0.96,
        "missing_data_indicator": 0,
    }

def simulate_scenario(history_frame: pd.DataFrame, profile: dict, name: str, model, features: list[str]):
    if name not in SCENARIOS:
        raise ValueError(f"unknown scenario: {name}")
    spec = SCENARIOS[name]
    history = history_frame[RAW_COLUMNS].copy().sort_values("timestamp")
    profile_df = pd.DataFrame([profile])
    current_features = build_features(profile_df, history).iloc[-1]
    baseline_probability = float(model.predict_proba(pd.DataFrame([current_features[features].to_dict()]))[0, 1])

    previous = history.iloc[-1].to_dict()
    future_rows = []
    trajectory = []
    working = history.copy()

    for step in range(1, 13):
        new_row = _next_observation(previous, profile, step, spec)
        future_rows.append(new_row)
        working = pd.concat([working, pd.DataFrame([new_row])], ignore_index=True)
        feature_row = build_features(profile_df, working).iloc[-1]
        probability = float(model.predict_proba(pd.DataFrame([feature_row[features].to_dict()]))[0, 1])
        trajectory.append({
            "minute": step * 5,
            "timestamp": pd.Timestamp(new_row["timestamp"]).isoformat(),
            "event_probability": round(probability, 4),
            "heart_rate_bpm": round(float(new_row["heart_rate_bpm"]), 1),
            "systolic_bp": round(float(new_row["systolic_bp"]), 1),
            "hrv_ms": round(float(new_row["hrv_ms"]), 1),
            "activity_state": new_row["activity_state"],
        })
        previous = new_row

    probabilities = [point["event_probability"] for point in trajectory]
    return {
        "scenario": name,
        "label": spec.label,
        "hypothetical": True,
        "baseline_probability": round(baseline_probability, 4),
        "end_probability": round(probabilities[-1], 4),
        "max_probability": round(max(probabilities), 4),
        "difference_at_60m": round(probabilities[-1] - baseline_probability, 4),
        "trajectory": trajectory,
        "assumptions": list(spec.assumptions),
        "warning": "Hypothetical observation-space trajectory; not a causal treatment-effect estimate.",
    }
