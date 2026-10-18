from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

STATIC = [
    "age", "bmi", "hypertension_history", "diabetes_status", "smoking_code",
]
DYNAMIC = [
    "heart_rate_bpm", "hrv_ms", "systolic_bp", "diastolic_bp", "pulse_pressure",
    "steps", "sensor_quality", "activity_code", "sleep_state",
    "hr_mean_15", "hr_mean_60", "hr_std_60", "hr_slope_15", "hr_slope_30",
    "hrv_mean_15", "hrv_mean_60", "hrv_slope_15", "hrv_slope_30",
    "sys_mean_15", "sys_mean_60", "sys_std_60", "sys_slope_15", "sys_slope_30",
    "dia_mean_60", "steps_sum_60", "quality_mean_60",
    "missing_ratio_60", "time_since_valid_minutes",
    "hour_sin", "hour_cos",
]
PERSONAL = [
    "hr_deviation", "sys_deviation", "dia_deviation",
    "hr_relative", "hr_baseline_units", "sys_baseline_units",
]

FORBIDDEN_MODEL_FIELDS = {
    "target_60m", "event_onset", "event_active",
    "_sim_episode", "external_perturbation",
    "latent_stress", "latent_autonomic_instability", "latent_hemodynamic_load",
    "latent_recovery_debt", "latent_deterioration",
}

def _slope(series: pd.Series, periods: int = 6) -> pd.Series:
    return (series - series.shift(periods)) / max(periods, 1)

def _time_since_valid(group: pd.DataFrame) -> pd.Series:
    missing = group["missing_data_indicator"].astype(int).to_numpy()
    values = np.zeros(len(group), dtype=float)
    run = 0
    for i, flag in enumerate(missing):
        run = run + 1 if flag else 0
        values[i] = run * 5.0
    return pd.Series(values, index=group.index)

def build_features(patients: pd.DataFrame, wearables: pd.DataFrame) -> pd.DataFrame:
    w = wearables.sort_values(["patient_id", "timestamp"]).copy()
    w["timestamp"] = pd.to_datetime(w["timestamp"])
    p = patients.copy()
    p["smoking_code"] = p["smoking_status"].map({"never": 0, "former": 1, "current": 2}).fillna(0)
    w["activity_code"] = w["activity_state"].map({"sleep": 0, "rest": 1, "active": 2}).fillna(1)

    profile_cols = [
        "patient_id", "age", "bmi", "hypertension_history", "diabetes_status", "smoking_code",
        "baseline_hr", "historical_systolic_bp", "historical_diastolic_bp",
    ]
    w = w.merge(p[profile_cols], on="patient_id", how="left", validate="many_to_one")

    freshness_parts = []
    for _, group in w.groupby("patient_id", sort=False):
        freshness_parts.append(_time_since_valid(group))
    w["time_since_valid_minutes"] = pd.concat(freshness_parts).sort_index()

    fallbacks = {
        "heart_rate_bpm": "baseline_hr",
        "systolic_bp": "historical_systolic_bp",
        "diastolic_bp": "historical_diastolic_bp",
    }
    for col in ["heart_rate_bpm", "hrv_ms", "systolic_bp", "diastolic_bp"]:
        w[col] = w.groupby("patient_id", sort=False)[col].ffill()
        if col in fallbacks:
            w[col] = w[col].fillna(w[fallbacks[col]])
        else:
            age_adjusted_hrv = np.clip(58 - 0.22 * (w["age"] - 45), 30, 62)
            w[col] = w[col].fillna(age_adjusted_hrv)

    w["pulse_pressure"] = w["systolic_bp"] - w["diastolic_bp"]

    g = w.groupby("patient_id", sort=False)
    w["hr_mean_15"] = g["heart_rate_bpm"].transform(lambda s: s.rolling(3, min_periods=1).mean())
    w["hr_mean_60"] = g["heart_rate_bpm"].transform(lambda s: s.rolling(12, min_periods=1).mean())
    w["hr_std_60"] = g["heart_rate_bpm"].transform(lambda s: s.rolling(12, min_periods=2).std()).fillna(0)
    w["hr_slope_15"] = g["heart_rate_bpm"].transform(lambda s: _slope(s, 3)).fillna(0)
    w["hr_slope_30"] = g["heart_rate_bpm"].transform(lambda s: _slope(s, 6)).fillna(0)

    w["hrv_mean_15"] = g["hrv_ms"].transform(lambda s: s.rolling(3, min_periods=1).mean())
    w["hrv_mean_60"] = g["hrv_ms"].transform(lambda s: s.rolling(12, min_periods=1).mean())
    w["hrv_slope_15"] = g["hrv_ms"].transform(lambda s: _slope(s, 3)).fillna(0)
    w["hrv_slope_30"] = g["hrv_ms"].transform(lambda s: _slope(s, 6)).fillna(0)

    w["sys_mean_15"] = g["systolic_bp"].transform(lambda s: s.rolling(3, min_periods=1).mean())
    w["sys_mean_60"] = g["systolic_bp"].transform(lambda s: s.rolling(12, min_periods=1).mean())
    w["sys_std_60"] = g["systolic_bp"].transform(lambda s: s.rolling(12, min_periods=2).std()).fillna(0)
    w["sys_slope_15"] = g["systolic_bp"].transform(lambda s: _slope(s, 3)).fillna(0)
    w["sys_slope_30"] = g["systolic_bp"].transform(lambda s: _slope(s, 6)).fillna(0)
    w["dia_mean_60"] = g["diastolic_bp"].transform(lambda s: s.rolling(12, min_periods=1).mean())

    w["steps_sum_60"] = g["steps"].transform(lambda s: s.rolling(12, min_periods=1).sum())
    w["quality_mean_60"] = g["sensor_quality"].transform(lambda s: s.rolling(12, min_periods=1).mean())
    w["missing_ratio_60"] = g["missing_data_indicator"].transform(lambda s: s.rolling(12, min_periods=1).mean())

    w["hr_deviation"] = w["heart_rate_bpm"] - w["baseline_hr"]
    w["sys_deviation"] = w["systolic_bp"] - w["historical_systolic_bp"]
    w["dia_deviation"] = w["diastolic_bp"] - w["historical_diastolic_bp"]
    w["hr_relative"] = w["heart_rate_bpm"] / w["baseline_hr"].clip(lower=1)
    w["hr_baseline_units"] = w["hr_deviation"] / 8.0
    w["sys_baseline_units"] = w["sys_deviation"] / 10.0

    hour = w["timestamp"].dt.hour + w["timestamp"].dt.minute / 60
    w["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    w["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    return w

def feature_groups():
    return {
        "ehr_only": STATIC,
        "wearable_only": DYNAMIC,
        "fusion": STATIC + DYNAMIC,
        "personalized": STATIC + DYNAMIC + PERSONAL,
    }

def assert_no_leakage(features: list[str]) -> None:
    overlap = FORBIDDEN_MODEL_FIELDS.intersection(features)
    if overlap:
        raise ValueError(f"forbidden leakage fields in schema: {sorted(overlap)}")

def load_feature_frame(root: Path | None = None) -> pd.DataFrame:
    root = root or Path(__file__).resolve().parents[1]
    patients = pd.read_csv(root/"data"/"sample_patients.csv")
    wearables = pd.read_csv(root/"data"/"sample_wearables.csv", parse_dates=["timestamp"])
    frame = build_features(patients, wearables)
    for features in feature_groups().values():
        assert_no_leakage(features)
    return frame
