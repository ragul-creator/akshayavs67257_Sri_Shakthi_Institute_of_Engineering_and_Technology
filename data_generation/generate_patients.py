from __future__ import annotations
import numpy as np
import pandas as pd

def generate_patients(n_patients: int = 60, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ids = [f"P{i:04d}" for i in range(1, n_patients + 1)]
    age = rng.integers(35, 82, n_patients)
    sex = rng.choice(["F", "M"], n_patients)
    height = np.where(sex == "M", rng.normal(174, 7, n_patients), rng.normal(162, 7, n_patients))
    bmi = np.clip(rng.normal(26.2, 4.2, n_patients), 18, 39)
    weight = bmi * (height / 100.0) ** 2
    hypertension = (rng.random(n_patients) < np.clip((age - 25) / 90, .12, .65)).astype(int)
    diabetes = (rng.random(n_patients) < np.clip((age - 20) / 170, .06, .35)).astype(int)
    smoking = rng.choice(["never", "former", "current"], n_patients, p=[.58, .27, .15])
    base_hr = np.clip(rng.normal(68 + 2*smoking.astype(str).astype(object).__eq__("current"), 7), 52, 88)
    base_sys = np.clip(rng.normal(116 + hypertension*15 + (age-50)*.12, 9), 96, 155)
    base_dia = np.clip(rng.normal(74 + hypertension*8, 7), 58, 98)
    return pd.DataFrame({
        "patient_id": ids, "age": age, "sex": sex,
        "height_cm": height.round(1), "weight_kg": weight.round(1), "bmi": bmi.round(1),
        "hypertension_history": hypertension, "diabetes_status": diabetes,
        "smoking_status": smoking, "medication_history": np.where(hypertension==1, "simulated_antihypertensive", "none"),
        "historical_systolic_bp": base_sys.round(1), "historical_diastolic_bp": base_dia.round(1),
        "baseline_hr": base_hr.round(1), "profile_creation_time": "2026-01-01T00:00:00Z",
    })

if __name__ == "__main__":
    from pathlib import Path
    out = Path(__file__).resolve().parents[1] / "data" / "sample_patients.csv"
    out.parent.mkdir(exist_ok=True)
    generate_patients().to_csv(out, index=False)
    print(out)
