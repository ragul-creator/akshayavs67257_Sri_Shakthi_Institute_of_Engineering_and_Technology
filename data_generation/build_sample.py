from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_generation.generate_patients import generate_patients
from data_generation.generate_wearables import generate_wearables
from data_generation.generate_events import derive_events_and_labels
from data_generation.validate_data import validate

PATIENTS = 120
DAYS = 3
PATIENT_SEED = 42
PHYSIOLOGY_SEED = 43

patients = generate_patients(PATIENTS, PATIENT_SEED)
wearables, latent = generate_wearables(patients, DAYS, PHYSIOLOGY_SEED, return_latent=True)
labeled, events = derive_events_and_labels(wearables, latent)
validate(patients, labeled)

patients.to_csv(ROOT/"data"/"sample_patients.csv", index=False)
labeled.to_csv(ROOT/"data"/"sample_wearables.csv", index=False)
latent.to_csv(ROOT/"data"/"sample_latent.csv", index=False)
events.to_csv(ROOT/"data"/"sample_events.csv", index=False)

report = {
    "patient_seed": PATIENT_SEED,
    "physiology_seed": PHYSIOLOGY_SEED,
    "patients": len(patients),
    "observations": len(labeled),
    "latent_rows": len(latent),
    "events": len(events),
    "cadence_minutes": 5,
    "days": DAYS,
    "event_source": "hidden_latent_deterioration_state",
    "synthetic_only": True,
}
(ROOT/"reports"/"data_generation_report.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
