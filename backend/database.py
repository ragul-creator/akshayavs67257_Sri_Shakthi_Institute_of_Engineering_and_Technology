from __future__ import annotations
from pathlib import Path
import json
import sqlite3
from datetime import datetime, timezone

class TwinStore:
    def __init__(self,path:Path):
        self.path=path
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self._init()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init(self):
        with self._connect() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS predictions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                observation_timestamp TEXT NOT NULL,
                probability REAL NOT NULL,
                risk_category TEXT NOT NULL,
                model_version TEXT NOT NULL,
                stored_at TEXT NOT NULL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS scenarios(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                scenario_name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                stored_at TEXT NOT NULL)""")

    def log_prediction(self,payload:dict):
        with self._connect() as c:
            c.execute("INSERT INTO predictions(patient_id,observation_timestamp,probability,risk_category,model_version,stored_at) VALUES(?,?,?,?,?,?)",
                (payload["patient_id"],payload["observation_timestamp"],payload["event_probability"],
                 payload["risk_category"],payload["model_version"],datetime.now(timezone.utc).isoformat()))

    def log_scenario(self,patient_id:str,payload:dict):
        with self._connect() as c:
            c.execute("INSERT INTO scenarios(patient_id,scenario_name,payload_json,stored_at) VALUES(?,?,?,?)",
                (patient_id,payload["scenario"],json.dumps(payload),datetime.now(timezone.utc).isoformat()))
