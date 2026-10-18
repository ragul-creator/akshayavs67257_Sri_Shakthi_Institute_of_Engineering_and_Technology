from __future__ import annotations

from pathlib import Path
import json
import joblib
import pandas as pd

from backend.database import TwinStore
from ml.explain import explain_prediction
from twin_engine.estimator import estimate_observed_state
from twin_engine.scenarios import simulate_scenario
from twin_engine.simulator import initial_cursor, advance_cursor

ROOT = Path(__file__).resolve().parents[1]

class TwinEngine:
    def __init__(self):
        self.patients = pd.read_csv(ROOT/"data"/"sample_patients.csv")
        self.features = pd.read_csv(ROOT/"data"/"features.csv", parse_dates=["timestamp"])
        self.features = self.features.sort_values(["patient_id", "timestamp"])
        self.model = joblib.load(ROOT/"models"/"cardio_twin_model.joblib")
        self.schema = json.loads((ROOT/"models"/"feature_schema.json").read_text())
        self.metadata = json.loads((ROOT/"models"/"model_metadata.json").read_text())
        self.evaluation = json.loads((ROOT/"reports"/"evaluation_results.json").read_text())
        multiseed_path = ROOT/"reports"/"multiseed_evaluation.json"
        if multiseed_path.exists():
            self.evaluation["multiseed"] = json.loads(multiseed_path.read_text())
        self.store = TwinStore(ROOT/"data"/"cardiotwin.db")
        self.cursors = {}
        self.histories = {}
        self.scenarios = {}

    def patient_ids(self):
        return self.patients["patient_id"].tolist()

    def profile(self, patient_id):
        row = self.patients[self.patients.patient_id == patient_id]
        if row.empty:
            raise KeyError(patient_id)
        return row.iloc[0].to_dict()

    def _frame(self, patient_id):
        frame = self.features[self.features.patient_id == patient_id].reset_index(drop=True)
        if frame.empty:
            raise KeyError(patient_id)
        return frame

    def reset(self, patient_id):
        frame = self._frame(patient_id)
        self.cursors[patient_id] = initial_cursor(len(frame), warmup_steps=24)
        self.histories[patient_id] = []
        self.scenarios[patient_id] = []
        return self.twin(patient_id)

    def _cursor(self, patient_id):
        if patient_id not in self.cursors:
            self.reset(patient_id)
        return self.cursors[patient_id]

    def _predict_row(self, row):
        features = self.schema["features"]
        x = pd.DataFrame([{name: float(row[name]) for name in features}])
        probability = float(self.model.predict_proba(x)[0, 1])
        threshold = float(self.metadata["threshold"])
        category = "prototype-alert" if probability >= threshold else "below-alert-threshold"
        return probability, category

    def forecast(self, patient_id):
        frame = self._frame(patient_id)
        row = frame.iloc[self._cursor(patient_id)]
        probability, category = self._predict_row(row)
        quality = {
            "status": (
                "limited"
                if row.missing_ratio_60 > 0.20
                or row.quality_mean_60 < 0.70
                or row.time_since_valid_minutes > 15
                else "adequate"
            ),
            "sensor_quality": round(float(row.sensor_quality), 3),
            "quality_mean_60": round(float(row.quality_mean_60), 3),
            "missing_ratio_60": round(float(row.missing_ratio_60), 3),
            "time_since_valid_minutes": round(float(row.time_since_valid_minutes), 1),
        }
        return {
            "patient_id": patient_id,
            "observation_timestamp": row.timestamp.isoformat(),
            "forecast_horizon_minutes": 60,
            "event_probability": round(probability, 4),
            "risk_category": category,
            "threshold": round(float(self.metadata["threshold"]), 4),
            "model_version": self.metadata["model_version"],
            "event_definition": "hidden synthetic deterioration-state onset within 60 minutes",
            "data_quality": quality,
            "estimated_state": estimate_observed_state(row),
            "explanation": explain_prediction(self.model, row, self.schema["features"]),
            "disclaimer": "Synthetic research prototype; not a diagnosis, triage output, or treatment recommendation.",
        }

    def twin(self, patient_id):
        profile = self.profile(patient_id)
        frame = self._frame(patient_id)
        cursor = self._cursor(patient_id)
        row = frame.iloc[cursor]
        forecast = self.forecast(patient_id)
        return {
            "patient_id": patient_id,
            "profile": profile,
            "simulation": {
                "cursor": cursor,
                "total": len(frame),
                "status": "ready",
                "cadence_minutes": 5,
                "progress": round(cursor / max(len(frame) - 1, 1), 4),
            },
            "current_state": {
                "timestamp": row.timestamp.isoformat(),
                "heart_rate_bpm": round(float(row.heart_rate_bpm), 1),
                "hrv_ms": round(float(row.hrv_ms), 1),
                "systolic_bp": round(float(row.systolic_bp), 1),
                "diastolic_bp": round(float(row.diastolic_bp), 1),
                "steps": int(row.steps),
                "activity_state": row.activity_state,
                "baseline_hr": round(float(row.baseline_hr), 1),
                "baseline_systolic_bp": round(float(row.historical_systolic_bp), 1),
                "hr_deviation": round(float(row.hr_deviation), 1),
                "systolic_deviation": round(float(row.sys_deviation), 1),
            },
            "estimated_state": forecast["estimated_state"],
            "forecast": forecast,
            "forecast_history": self.histories.get(patient_id, [])[-48:],
            "scenario_history": self.scenarios.get(patient_id, [])[-10:],
            "synthetic": True,
        }

    def step(self, patient_id, steps=1):
        frame = self._frame(patient_id)
        self.cursors[patient_id] = advance_cursor(
            self._cursor(patient_id), len(frame), max(1, int(steps))
        )
        forecast = self.forecast(patient_id)
        record = {
            "timestamp": forecast["observation_timestamp"],
            "event_probability": forecast["event_probability"],
            "risk_category": forecast["risk_category"],
            "physiologic_strain": forecast["estimated_state"]["physiologic_strain"],
            "confidence": forecast["estimated_state"]["confidence"],
        }
        self.histories.setdefault(patient_id, []).append(record)
        self.store.log_prediction(forecast)
        return self.twin(patient_id)

    def recent_observations(self, patient_id, n=72):
        frame = self._frame(patient_id)
        cursor = self._cursor(patient_id)
        cols = [
            "timestamp", "heart_rate_bpm", "systolic_bp", "diastolic_bp",
            "hrv_ms", "steps", "activity_state", "sensor_quality",
            "missing_data_indicator",
        ]
        out = frame.iloc[max(0, cursor-n+1):cursor+1][cols].copy()
        out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        return out.to_dict(orient="records")

    def retrospective(self, patient_id, n=288):
        """Past/current labels for evaluation mode only; never used by live inference."""
        frame = self._frame(patient_id)
        cursor = self._cursor(patient_id)
        cols = [
            "timestamp", "heart_rate_bpm", "systolic_bp", "hrv_ms",
            "event_onset", "event_active", "target_60m",
        ]
        out = frame.iloc[max(0, cursor-n+1):cursor+1][cols].copy()
        out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        return {
            "mode": "retrospective_evaluation_only",
            "patient_id": patient_id,
            "rows": out.to_dict(orient="records"),
        }

    def run_scenario(self, patient_id, name):
        frame = self._frame(patient_id)
        cursor = self._cursor(patient_id)
        history = frame.iloc[max(0, cursor-35):cursor+1].copy()
        result = simulate_scenario(
            history_frame=history,
            profile=self.profile(patient_id),
            name=name,
            model=self.model,
            features=self.schema["features"],
        )
        self.scenarios.setdefault(patient_id, []).append(result)
        self.store.log_scenario(patient_id, result)
        return result
