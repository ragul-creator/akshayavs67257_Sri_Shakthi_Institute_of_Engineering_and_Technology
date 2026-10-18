from __future__ import annotations
from pathlib import Path
import json
import joblib
import pandas as pd

from backend.database import TwinStore
from ml.explain import explain_prediction
from twin_engine.scenarios import apply_scenario
from twin_engine.simulator import initial_cursor,advance_cursor

ROOT=Path(__file__).resolve().parents[1]

class TwinEngine:
    def __init__(self):
        self.patients=pd.read_csv(ROOT/"data"/"sample_patients.csv")
        self.features=pd.read_csv(ROOT/"data"/"features.csv",parse_dates=["timestamp"])
        self.features=self.features.sort_values(["patient_id","timestamp"])
        self.model=joblib.load(ROOT/"models"/"cardio_twin_model.joblib")
        self.schema=json.loads((ROOT/"models"/"feature_schema.json").read_text())
        self.metadata=json.loads((ROOT/"models"/"model_metadata.json").read_text())
        self.evaluation=json.loads((ROOT/"reports"/"evaluation_results.json").read_text())
        self.store=TwinStore(ROOT/"data"/"cardiotwin.db")
        self.cursors={}; self.histories={}; self.scenarios={}

    def patient_ids(self):
        return self.patients["patient_id"].tolist()

    def profile(self,pid):
        row=self.patients[self.patients.patient_id==pid]
        if row.empty: raise KeyError(pid)
        return row.iloc[0].to_dict()

    def _frame(self,pid):
        g=self.features[self.features.patient_id==pid].reset_index(drop=True)
        if g.empty: raise KeyError(pid)
        return g

    def reset(self,pid):
        g=self._frame(pid)
        self.cursors[pid]=initial_cursor(len(g))
        self.histories[pid]=[]
        self.scenarios[pid]=[]
        return self.twin(pid)

    def _cursor(self,pid):
        if pid not in self.cursors:
            self.reset(pid)
        return self.cursors[pid]

    def _predict_row(self,row):
        feats=self.schema["features"]
        X=pd.DataFrame([{f:float(row[f]) for f in feats}])
        prob=float(self.model.predict_proba(X)[0,1])
        threshold=float(self.metadata["threshold"])
        return prob,("prototype-alert" if prob>=threshold else "no-alert")

    def forecast(self,pid):
        g=self._frame(pid); row=g.iloc[self._cursor(pid)]
        prob,category=self._predict_row(row)
        return {
            "patient_id":pid,
            "observation_timestamp":row.timestamp.isoformat(),
            "forecast_horizon_minutes":60,
            "event_probability":round(prob,4),
            "risk_category":category,
            "threshold":round(float(self.metadata["threshold"]),4),
            "model_version":self.metadata["model_version"],
            "data_quality":{
                "status":"limited" if row.missing_ratio_60>.25 or row.sensor_quality<.6 else "adequate",
                "sensor_quality":round(float(row.sensor_quality),3),
                "missing_ratio_60":round(float(row.missing_ratio_60),3),
            },
            "explanation":explain_prediction(self.model,row,self.schema["features"]),
            "disclaimer":"Synthetic research prototype; not a diagnosis or medical triage output.",
        }

    def twin(self,pid):
        p=self.profile(pid); g=self._frame(pid); i=self._cursor(pid); row=g.iloc[i]; fc=self.forecast(pid)
        return {
            "patient_id":pid,
            "profile":p,
            "simulation":{"cursor":i,"total":len(g),"status":"ready"},
            "current_state":{
                "timestamp":row.timestamp.isoformat(),
                "heart_rate_bpm":round(float(row.heart_rate_bpm),1),
                "hrv_ms":round(float(row.hrv_ms),1),
                "systolic_bp":round(float(row.systolic_bp),1),
                "diastolic_bp":round(float(row.diastolic_bp),1),
                "steps":int(row.steps),
                "activity_state":row.activity_state,
                "baseline_hr":round(float(row.baseline_hr),1),
                "baseline_systolic_bp":round(float(row.historical_systolic_bp),1),
            },
            "forecast":fc,
            "history":self.histories.get(pid,[])[-30:],
            "synthetic":True,
        }

    def step(self,pid,steps=1):
        g=self._frame(pid)
        self.cursors[pid]=advance_cursor(self._cursor(pid),len(g),max(1,int(steps)))
        fc=self.forecast(pid)
        record={"timestamp":fc["observation_timestamp"],"event_probability":fc["event_probability"],
                "risk_category":fc["risk_category"]}
        self.histories.setdefault(pid,[]).append(record)
        self.store.log_prediction(fc)
        return self.twin(pid)

    def recent_observations(self,pid,n=36):
        g=self._frame(pid); i=self._cursor(pid)
        cols=["timestamp","heart_rate_bpm","systolic_bp","diastolic_bp","hrv_ms","sensor_quality"]
        out=g.iloc[max(0,i-n+1):i+1][cols].copy()
        out["timestamp"]=out["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        return out.to_dict(orient="records")

    def run_scenario(self,pid,name):
        g=self._frame(pid)
        source=g.iloc[self._cursor(pid)]
        original_prob,_=self._predict_row(source)
        row,assumptions=apply_scenario(source,name)
        scenario_prob,_=self._predict_row(row)
        result={
            "scenario":name,
            "hypothetical":True,
            "baseline_probability":round(original_prob,4),
            "scenario_probability":round(scenario_prob,4),
            "difference":round(scenario_prob-original_prob,4),
            "assumptions":assumptions,
            "warning":"Scenario output is not a causal treatment-effect estimate.",
        }
        self.scenarios.setdefault(pid,[]).append(result)
        self.store.log_scenario(pid,result)
        return result
