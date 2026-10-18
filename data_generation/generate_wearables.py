from __future__ import annotations
import numpy as np
import pandas as pd

REFERENCE_STEPS=144  # first 12 hours reserved for baseline estimation

def _event_starts(rng,periods,count):
    candidates=np.arange(REFERENCE_STEPS+12,periods-36)
    rng.shuffle(candidates)
    chosen=[]
    for c in candidates:
        if all(abs(int(c)-s)>=36 for s in chosen):
            chosen.append(int(c))
        if len(chosen)>=count:
            break
    return sorted(chosen)

def generate_wearables(patients: pd.DataFrame, days: int = 2, seed: int = 43) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    periods = days * 24 * 12
    if periods <= REFERENCE_STEPS+48:
        raise ValueError("simulation needs at least one day")
    start = pd.Timestamp("2026-01-01 00:00:00")
    rows = []
    for p in patients.itertuples(index=False):
        times = pd.date_range(start, periods=periods, freq="5min")
        event_starts = _event_starts(rng,periods,max(2,days))
        for i, ts in enumerate(times):
            hour = ts.hour + ts.minute/60
            sleep = int(hour >= 23 or hour < 6)
            active_prob = 0.03 if sleep else 0.18
            active = rng.random() < active_prob
            circ = 3*np.sin(2*np.pi*(hour-8)/24)
            hr = p.baseline_hr + circ - 7*sleep + (18 if active else 0) + rng.normal(0, 3.0)
            sys = p.historical_systolic_bp + 0.7*circ + (10 if active else 0) + rng.normal(0, 4.0)
            dia = p.historical_diastolic_bp + 0.3*circ + (5 if active else 0) + rng.normal(0, 3.0)
            hrv = 52 - .35*(hr-p.baseline_hr) + 8*sleep + rng.normal(0, 6)
            episode = 0
            for onset in event_starts:
                dt = i - onset
                if -9 <= dt < 0:
                    ramp = (dt + 10) / 10
                    hr += 13*ramp
                    sys += 10*ramp
                    hrv -= 8*ramp
                elif 0 <= dt < 6:
                    episode = 1
                    hr += 30 + rng.normal(0, 1.5)
                    sys += 23 + rng.normal(0, 1.5)
                    dia += 10 + rng.normal(0, 2)
                    hrv -= 14
            missing = int(rng.random() < .018)
            quality = float(np.clip(rng.normal(.94 if not missing else .35, .07), 0, 1))
            rows.append({
                "timestamp": ts, "patient_id": p.patient_id,
                "heart_rate_bpm": np.nan if missing else round(hr,1),
                "hrv_ms": np.nan if missing else round(max(hrv, 12),1),
                "systolic_bp": np.nan if missing else round(sys,1),
                "diastolic_bp": np.nan if missing else round(dia,1),
                "steps": 0 if sleep else int(rng.poisson(2 if not active else 55)),
                "activity_state": "sleep" if sleep else ("active" if active else "rest"),
                "sleep_state": sleep, "sensor_quality": round(quality,3),
                "missing_data_indicator": missing, "_sim_episode": episode,
            })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    from pathlib import Path
    from generate_patients import generate_patients
    root = Path(__file__).resolve().parents[1]
    generate_wearables(generate_patients()).to_csv(root/"data"/"sample_wearables.csv", index=False)
