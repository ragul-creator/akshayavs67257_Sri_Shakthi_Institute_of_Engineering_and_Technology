from __future__ import annotations
import pandas as pd
from data_generation.physiology import simulate_cohort

def generate_wearables(patients: pd.DataFrame, days: int = 3, seed: int = 43, return_latent: bool = False):
    wearables, latent = simulate_cohort(patients, days=days, seed=seed)
    return (wearables, latent) if return_latent else wearables

if __name__ == "__main__":
    from pathlib import Path
    from data_generation.generate_patients import generate_patients
    root = Path(__file__).resolve().parents[1]
    p = generate_patients(120)
    w, l = generate_wearables(p, days=3, return_latent=True)
    w.to_csv(root/"data"/"sample_wearables.csv", index=False)
    l.to_csv(root/"data"/"sample_latent.csv", index=False)
