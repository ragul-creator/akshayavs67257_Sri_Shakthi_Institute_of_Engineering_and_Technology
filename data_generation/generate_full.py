from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_generation.generate_patients import generate_patients
from data_generation.generate_wearables import generate_wearables
from data_generation.generate_events import derive_events_and_labels
from data_generation.validate_data import validate

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--patients", type=int, default=500)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--seed", type=int, default=4200)
    args = parser.parse_args()

    patients = generate_patients(args.patients, args.seed)
    wearables, latent = generate_wearables(
        patients, args.days, args.seed + 1, return_latent=True
    )
    labeled, events = derive_events_and_labels(wearables, latent)
    validate(patients, labeled)

    patients.to_csv(ROOT/"data"/"full_patients.csv", index=False)
    labeled.to_csv(ROOT/"data"/"full_wearables.csv", index=False)
    latent.to_csv(ROOT/"data"/"full_latent.csv", index=False)
    events.to_csv(ROOT/"data"/"full_events.csv", index=False)

    report = {
        "patients": len(patients),
        "days": args.days,
        "observations": len(labeled),
        "latent_rows": len(latent),
        "events": len(events),
        "patient_seed": args.seed,
        "physiology_seed": args.seed + 1,
        "event_source": "hidden_latent_deterioration_state",
        "synthetic_only": True,
    }
    (ROOT/"reports"/"full_data_generation_report.json").write_text(
        json.dumps(report, indent=2)
    )
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
