from __future__ import annotations

from pathlib import Path
import json
import joblib
import numpy as np

from ml.preprocessing import load_feature_frame
from ml.train import split_patients, metrics

ROOT = Path(__file__).resolve().parents[1]

def main():
    frame = load_feature_frame(ROOT)
    _, _, test_ids = split_patients(frame)
    test = frame[(frame.patient_id.isin(test_ids)) & (frame.event_active == 0)].copy()

    schema = json.loads((ROOT/"models"/"feature_schema.json").read_text())
    metadata = json.loads((ROOT/"models"/"model_metadata.json").read_text())
    model = joblib.load(ROOT/"models"/"cardio_twin_model.joblib")
    features = schema["features"]
    threshold = float(metadata["threshold"])
    y = test.target_60m.astype(int)
    clean = model.predict_proba(test[features])[:, 1]

    rng = np.random.default_rng(2026)

    noisy = test[features].copy()
    noise_map = {
        "heart_rate_bpm": 5, "hr_mean_15": 4, "hr_mean_60": 3,
        "systolic_bp": 7, "sys_mean_15": 5, "sys_mean_60": 4,
        "diastolic_bp": 4, "dia_mean_60": 3,
        "hrv_ms": 7, "hrv_mean_15": 5, "hrv_mean_60": 4,
    }
    for col, sd in noise_map.items():
        if col in noisy:
            noisy[col] = noisy[col] + rng.normal(0, sd, len(noisy))
    noise_prob = model.predict_proba(noisy)[:, 1]

    missing = test[features].copy()
    mask = rng.random(len(missing)) < 0.15
    replacements = {
        "heart_rate_bpm": "hr_mean_60",
        "hrv_ms": "hrv_mean_60",
        "systolic_bp": "sys_mean_60",
        "diastolic_bp": "dia_mean_60",
    }
    for target, source in replacements.items():
        if target in missing and source in test:
            missing.loc[mask, target] = test.loc[mask, source]
    if "sensor_quality" in missing:
        missing.loc[mask, "sensor_quality"] = np.minimum(
            missing.loc[mask, "sensor_quality"], 0.45
        )
    if "quality_mean_60" in missing:
        missing.loc[mask, "quality_mean_60"] = np.minimum(
            missing.loc[mask, "quality_mean_60"], 0.65
        )
    if "missing_ratio_60" in missing:
        missing.loc[mask, "missing_ratio_60"] = np.minimum(
            1, missing.loc[mask, "missing_ratio_60"] + 0.20
        )
    missing_prob = model.predict_proba(missing)[:, 1]

    report = json.loads((ROOT/"reports"/"evaluation_results.json").read_text())
    report["robustness"] = {
        "clean_reference": metrics(y, clean, threshold),
        "added_sensor_noise": metrics(y, noise_prob, threshold),
        "simulated_current_reading_loss_15pct": metrics(y, missing_prob, threshold),
    }
    (ROOT/"reports"/"evaluation_results.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["robustness"], indent=2))

if __name__ == "__main__":
    main()
