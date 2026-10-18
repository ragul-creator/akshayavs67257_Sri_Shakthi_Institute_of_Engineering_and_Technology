from __future__ import annotations
import pandas as pd

def validate(patients: pd.DataFrame, wearables: pd.DataFrame) -> None:
    assert patients["patient_id"].is_unique
    assert set(wearables["patient_id"]).issubset(set(patients["patient_id"]))
    assert not wearables.duplicated(["patient_id","timestamp"]).any()
    assert wearables["sensor_quality"].between(0,1).all()
    assert set(wearables["target_60m"].dropna().unique()).issubset({0,1})

if __name__ == "__main__":
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    p = pd.read_csv(root/"data"/"sample_patients.csv")
    w = pd.read_csv(root/"data"/"sample_wearables.csv")
    validate(p,w)
    print(f"validated {len(p)} patients and {len(w)} observations")
