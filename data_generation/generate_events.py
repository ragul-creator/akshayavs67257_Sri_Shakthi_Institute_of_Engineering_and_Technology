from __future__ import annotations
import numpy as np
import pandas as pd

HORIZON_STEPS = 12
ONSET_THRESHOLD = 0.72
END_THRESHOLD = 0.48
MIN_ONSET_STEPS = 4
MIN_END_STEPS = 3

def _segments(values: np.ndarray):
    active = False
    onset_candidate = 0
    end_candidate = 0
    start = None
    segments = []
    for i, value in enumerate(values):
        if not active:
            onset_candidate = onset_candidate + 1 if value >= ONSET_THRESHOLD else 0
            if onset_candidate >= MIN_ONSET_STEPS:
                start = i - MIN_ONSET_STEPS + 1
                active = True
                end_candidate = 0
        else:
            end_candidate = end_candidate + 1 if value < END_THRESHOLD else 0
            if end_candidate >= MIN_END_STEPS:
                end = i - MIN_END_STEPS
                segments.append((start, end))
                active = False
                onset_candidate = 0
                start = None
    if active and start is not None:
        segments.append((start, len(values) - 1))
    return segments

def derive_events_and_labels(wearables: pd.DataFrame, latent: pd.DataFrame):
    keys = ["patient_id", "timestamp"]
    w = wearables.sort_values(keys).copy()
    l = latent.sort_values(keys).copy()
    w["timestamp"] = pd.to_datetime(w["timestamp"])
    l["timestamp"] = pd.to_datetime(l["timestamp"])

    if len(w) != len(l):
        raise ValueError("wearable and latent streams must have equal length")
    merged_keys = w[keys].reset_index(drop=True).equals(l[keys].reset_index(drop=True))
    if not merged_keys:
        raise ValueError("wearable and latent streams are not aligned")

    w["event_onset"] = 0
    w["event_active"] = 0
    w["target_60m"] = 0
    events = []

    latent_groups = {pid: g.reset_index(drop=True) for pid, g in l.groupby("patient_id", sort=False)}
    for pid, g in w.groupby("patient_id", sort=False):
        idx = g.index.to_list()
        lg = latent_groups[pid]
        values = lg["latent_deterioration"].to_numpy(dtype=float)
        for start, end in _segments(values):
            w.loc[idx[start], "event_onset"] = 1
            w.loc[idx[start:end + 1], "event_active"] = 1
            events.append({
                "patient_id": pid,
                "event_onset": w.loc[idx[start], "timestamp"],
                "event_end": w.loc[idx[end], "timestamp"],
                "latent_onset_threshold": ONSET_THRESHOLD,
                "latent_end_threshold": END_THRESHOLD,
                "minimum_onset_minutes": MIN_ONSET_STEPS * 5,
                "definition": "hidden latent deterioration state crossing; not defined from observed HR/BP",
            })
            for pos in range(max(0, start - HORIZON_STEPS), start):
                if w.loc[idx[pos], "event_active"] == 0:
                    w.loc[idx[pos], "target_60m"] = 1
    return w, pd.DataFrame(events)

if __name__ == "__main__":
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    w = pd.read_csv(root/"data"/"sample_wearables.csv", parse_dates=["timestamp"])
    l = pd.read_csv(root/"data"/"sample_latent.csv", parse_dates=["timestamp"])
    labeled, events = derive_events_and_labels(w, l)
    labeled.to_csv(root/"data"/"sample_wearables.csv", index=False)
    events.to_csv(root/"data"/"sample_events.csv", index=False)
