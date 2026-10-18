from pathlib import Path
import json
from generate_patients import generate_patients
from generate_wearables import generate_wearables
from generate_events import derive_events_and_labels
from validate_data import validate

ROOT = Path(__file__).resolve().parents[1]
p = generate_patients()
raw = generate_wearables(p)
w, e = derive_events_and_labels(raw)
w = w.drop(columns=["_sim_episode"])
validate(p,w)
p.to_csv(ROOT/"data"/"sample_patients.csv", index=False)
w.to_csv(ROOT/"data"/"sample_wearables.csv", index=False)
e.to_csv(ROOT/"data"/"sample_events.csv", index=False)
report = {"seed_patients":42,"seed_wearables":43,"patients":len(p),"observations":len(w),
          "events":len(e),"cadence_minutes":5,"days":2,"synthetic_only":True}
(ROOT/"reports"/"data_generation_report.json").write_text(json.dumps(report, indent=2))
print(report)
