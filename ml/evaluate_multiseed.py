from __future__ import annotations

from pathlib import Path
import json
import joblib
import numpy as np

from data_generation.generate_patients import generate_patients
from data_generation.generate_wearables import generate_wearables
from data_generation.generate_events import derive_events_and_labels
from ml.preprocessing import build_features
from ml.train import metrics, event_metrics

ROOT = Path(__file__).resolve().parents[1]
COHORTS = [
    {"patient_seed": 5101, "physiology_seed": 101},
    {"patient_seed": 5202, "physiology_seed": 202},
    {"patient_seed": 5303, "physiology_seed": 303},
]

def main():
    model = joblib.load(ROOT/"models"/"cardio_twin_model.joblib")
    schema = json.loads((ROOT/"models"/"feature_schema.json").read_text())
    metadata = json.loads((ROOT/"models"/"model_metadata.json").read_text())
    features = schema["features"]
    threshold = float(metadata["threshold"])

    cohorts = []
    for config in COHORTS:
        patients = generate_patients(50, config["patient_seed"])
        wearables, latent = generate_wearables(
            patients, days=2, seed=config["physiology_seed"], return_latent=True
        )
        labeled, events = derive_events_and_labels(wearables, latent)
        frame = build_features(patients, labeled)
        full_prob = model.predict_proba(frame[features])[:, 1]
        eligible = frame.event_active == 0
        row_metrics = metrics(
            frame.loc[eligible, "target_60m"].astype(int),
            full_prob[eligible.to_numpy()],
            threshold,
        )
        event = event_metrics(frame, full_prob, threshold)
        cohorts.append({
            **config,
            "patients": int(frame.patient_id.nunique()),
            "rows": int(len(frame)),
            "events": int(len(events)),
            "eligible_positive_rate": float(frame.loc[eligible, "target_60m"].mean()),
            "row_metrics": row_metrics,
            "event_metrics": event,
        })

    summary = {}
    for key in ["roc_auc", "pr_auc", "f1", "precision", "recall", "brier"]:
        values = np.array([c["row_metrics"][key] for c in cohorts], dtype=float)
        summary[key] = {"mean": float(values.mean()), "std": float(values.std(ddof=1))}
    for key in ["event_detection_rate", "false_alerts_per_patient_day"]:
        values = np.array([c["event_metrics"][key] for c in cohorts], dtype=float)
        summary[key] = {"mean": float(values.mean()), "std": float(values.std(ddof=1))}

    report = {
        "description": "Out-of-seed synthetic stress test; not external clinical validation.",
        "model_version": metadata["model_version"],
        "cohorts": cohorts,
        "summary": summary,
    }
    (ROOT/"reports"/"multiseed_evaluation.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
