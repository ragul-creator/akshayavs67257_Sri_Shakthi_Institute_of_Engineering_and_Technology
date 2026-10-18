from __future__ import annotations
import argparse
from pathlib import Path
import json
from generate_patients import generate_patients
from generate_wearables import generate_wearables
from generate_events import derive_events_and_labels
from validate_data import validate

ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--patients",type=int,default=500)
    ap.add_argument("--days",type=int,default=7)
    ap.add_argument("--seed",type=int,default=4200)
    args=ap.parse_args()
    patients=generate_patients(args.patients,args.seed)
    raw=generate_wearables(patients,args.days,args.seed+1)
    wearables,events=derive_events_and_labels(raw)
    wearables=wearables.drop(columns=["_sim_episode"],errors="ignore")
    validate(patients,wearables)
    patients.to_csv(ROOT/"data"/"full_patients.csv",index=False)
    wearables.to_csv(ROOT/"data"/"full_wearables.csv",index=False)
    events.to_csv(ROOT/"data"/"full_events.csv",index=False)
    report={"patients":len(patients),"days":args.days,"observations":len(wearables),
            "events":len(events),"patient_seed":args.seed,"wearable_seed":args.seed+1,
            "synthetic_only":True}
    (ROOT/"reports"/"full_data_generation_report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
