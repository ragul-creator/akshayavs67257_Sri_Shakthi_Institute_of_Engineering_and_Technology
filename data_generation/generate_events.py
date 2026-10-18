from __future__ import annotations
import numpy as np
import pandas as pd

HORIZON_STEPS=12
REFERENCE_STEPS=144
HR_DELTA_THRESHOLD=22.0
SBP_DELTA_THRESHOLD=17.0
MIN_DURATION_STEPS=4

def _runs(mask):
    starts=[]; i=0; n=len(mask)
    while i<n:
        if not mask[i]:
            i+=1; continue
        j=i
        while j+1<n and mask[j+1]:
            j+=1
        if j-i+1>=MIN_DURATION_STEPS:
            starts.append((i,j))
        i=j+1
    return starts

def derive_events_and_labels(wearables: pd.DataFrame):
    df=wearables.sort_values(["patient_id","timestamp"]).copy()
    df["event_onset"]=0
    df["event_active"]=0
    df["target_60m"]=0
    events=[]
    for pid,g in df.groupby("patient_id",sort=False):
        idx=g.index.to_list()
        ref=g.iloc[:REFERENCE_STEPS]
        baseline_hr=float(ref["heart_rate_bpm"].median(skipna=True))
        baseline_sys=float(ref["systolic_bp"].median(skipna=True))
        hr=g["heart_rate_bpm"].to_numpy(dtype=float)
        sbp=g["systolic_bp"].to_numpy(dtype=float)
        valid=(g["missing_data_indicator"].to_numpy()==0)&np.isfinite(hr)&np.isfinite(sbp)
        qualifies=valid&(hr>=baseline_hr+HR_DELTA_THRESHOLD)&(sbp>=baseline_sys+SBP_DELTA_THRESHOLD)
        for start,end in _runs(qualifies):
            df.loc[idx[start],"event_onset"]=1
            for pos in range(start,end+1):
                df.loc[idx[pos],"event_active"]=1
            events.append({
                "patient_id":pid,
                "event_onset":df.loc[idx[start],"timestamp"],
                "event_end":df.loc[idx[end],"timestamp"],
                "baseline_hr":round(baseline_hr,2),
                "baseline_systolic_bp":round(baseline_sys,2),
                "hr_delta_threshold":HR_DELTA_THRESHOLD,
                "sbp_delta_threshold":SBP_DELTA_THRESHOLD,
                "minimum_duration_minutes":MIN_DURATION_STEPS*5,
                "baseline_reference_hours":REFERENCE_STEPS*5/60,
            })
            for pos in range(max(0,start-HORIZON_STEPS),start):
                if df.loc[idx[pos],"event_active"]==0:
                    df.loc[idx[pos],"target_60m"]=1
    return df,pd.DataFrame(events)

if __name__ == "__main__":
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    w=pd.read_csv(root/"data"/"sample_wearables.csv",parse_dates=["timestamp"])
    labeled,events=derive_events_and_labels(w)
    labeled.drop(columns=[c for c in ["_sim_episode"] if c in labeled]).to_csv(root/"data"/"sample_wearables.csv",index=False)
    events.to_csv(root/"data"/"sample_events.csv",index=False)
