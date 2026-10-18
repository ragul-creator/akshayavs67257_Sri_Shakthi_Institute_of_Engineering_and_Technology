from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

STATIC = ["age","bmi","hypertension_history","diabetes_status","smoking_code"]
WEARABLE = ["heart_rate_bpm","hrv_ms","systolic_bp","diastolic_bp","steps","sensor_quality",
            "activity_code","sleep_state","hr_mean_60","hr_std_60","hr_delta_30",
            "hrv_mean_60","sys_mean_60","dia_mean_60","missing_ratio_60","hour_sin","hour_cos"]
PERSONAL = ["hr_deviation","sys_deviation","dia_deviation","hr_relative"]

def build_features(patients: pd.DataFrame, wearables: pd.DataFrame) -> pd.DataFrame:
    w = wearables.sort_values(["patient_id","timestamp"]).copy()
    w["timestamp"] = pd.to_datetime(w["timestamp"])
    p = patients.copy()
    p["smoking_code"] = p["smoking_status"].map({"never":0,"former":1,"current":2}).fillna(0)
    w["activity_code"] = w["activity_state"].map({"sleep":0,"rest":1,"active":2}).fillna(1)
    w = w.merge(p[["patient_id","age","bmi","hypertension_history","diabetes_status","smoking_code",
                   "baseline_hr","historical_systolic_bp","historical_diastolic_bp"]], on="patient_id", how="left")

    for col, fallback in [("heart_rate_bpm","baseline_hr"),("hrv_ms",None),
                          ("systolic_bp","historical_systolic_bp"),("diastolic_bp","historical_diastolic_bp")]:
        w[col] = w.groupby("patient_id")[col].ffill()
        if fallback:
            w[col] = w[col].fillna(w[fallback])
        else:
            w[col] = w[col].fillna(50.0)

    g = w.groupby("patient_id", sort=False)
    w["hr_mean_60"] = g["heart_rate_bpm"].transform(lambda s: s.rolling(12, min_periods=1).mean())
    w["hr_std_60"] = g["heart_rate_bpm"].transform(lambda s: s.rolling(12, min_periods=1).std()).fillna(0)
    w["hr_delta_30"] = w["heart_rate_bpm"] - g["heart_rate_bpm"].shift(6)
    w["hrv_mean_60"] = g["hrv_ms"].transform(lambda s: s.rolling(12, min_periods=1).mean())
    w["sys_mean_60"] = g["systolic_bp"].transform(lambda s: s.rolling(12, min_periods=1).mean())
    w["dia_mean_60"] = g["diastolic_bp"].transform(lambda s: s.rolling(12, min_periods=1).mean())
    w["missing_ratio_60"] = g["missing_data_indicator"].transform(lambda s: s.rolling(12, min_periods=1).mean())
    w["hr_deviation"] = w["heart_rate_bpm"] - w["baseline_hr"]
    w["sys_deviation"] = w["systolic_bp"] - w["historical_systolic_bp"]
    w["dia_deviation"] = w["diastolic_bp"] - w["historical_diastolic_bp"]
    w["hr_relative"] = w["heart_rate_bpm"] / w["baseline_hr"].clip(lower=1)
    hour = w["timestamp"].dt.hour + w["timestamp"].dt.minute/60
    w["hour_sin"] = np.sin(2*np.pi*hour/24)
    w["hour_cos"] = np.cos(2*np.pi*hour/24)
    w["hr_delta_30"] = w["hr_delta_30"].fillna(0)
    return w

def feature_groups():
    return {
        "ehr_only": STATIC,
        "wearable_only": WEARABLE,
        "fusion": STATIC + WEARABLE,
        "personalized": STATIC + WEARABLE + PERSONAL,
    }

def load_feature_frame(root: Path | None = None) -> pd.DataFrame:
    root = root or Path(__file__).resolve().parents[1]
    p = pd.read_csv(root/"data"/"sample_patients.csv")
    w = pd.read_csv(root/"data"/"sample_wearables.csv", parse_dates=["timestamp"])
    return build_features(p,w)

