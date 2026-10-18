from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

CADENCE_MINUTES = 5
REFERENCE_STEPS = 12 * 12

@dataclass(frozen=True)
class SimulationConfig:
    days: int = 3
    cadence_minutes: int = CADENCE_MINUTES
    shock_count_per_day: float = 0.7
    dropout_probability: float = 0.018

def _episode_forcing(periods: int, rng: np.random.Generator, count: int) -> np.ndarray:
    forcing = np.zeros(periods, dtype=float)
    start_min = REFERENCE_STEPS + 24
    candidates = np.arange(start_min, max(start_min + 1, periods - 48))
    if len(candidates) == 0:
        return forcing
    rng.shuffle(candidates)
    starts = []
    for candidate in candidates:
        if all(abs(int(candidate) - s) >= 60 for s in starts):
            starts.append(int(candidate))
        if len(starts) >= count:
            break
    for start in starts:
        # Smooth onset, plateau, recovery. This is an unobserved external perturbation.
        for offset in range(-12, 31):
            i = start + offset
            if i < 0 or i >= periods:
                continue
            if offset < 0:
                value = (offset + 12) / 12
            elif offset <= 10:
                value = 1.0
            else:
                value = max(0.0, 1.0 - (offset - 10) / 20)
            forcing[i] = max(forcing[i], value)
    return forcing

def simulate_patient(patient, config: SimulationConfig, rng: np.random.Generator):
    periods = config.days * 24 * 60 // config.cadence_minutes
    start = pd.Timestamp("2026-01-01 00:00:00")
    times = pd.date_range(start, periods=periods, freq=f"{config.cadence_minutes}min")
    risk = (
        0.15
        + 0.004 * max(float(patient.age) - 45, 0)
        + 0.10 * float(patient.hypertension_history)
        + 0.08 * float(patient.diabetes_status)
        + (0.07 if patient.smoking_status == "current" else 0.02 if patient.smoking_status == "former" else 0)
    )
    episode_count = max(1, int(round(config.days * config.shock_count_per_day * (0.75 + risk))))
    forcing = _episode_forcing(periods, rng, episode_count)

    stress = 0.18 + 0.08 * rng.random()
    autonomic = 0.10 + 0.05 * rng.random()
    hemodynamic = 0.12 + 0.05 * rng.random()
    recovery_debt = 0.12 + 0.04 * rng.random()
    deterioration = 0.05

    wearables = []
    latent = []

    for i, ts in enumerate(times):
        hour = ts.hour + ts.minute / 60
        circadian = np.sin(2 * np.pi * (hour - 8) / 24)
        sleep = int(hour >= 23 or hour < 6)
        active_probability = 0.025 if sleep else 0.16 + 0.04 * max(circadian, 0)
        active = int(rng.random() < active_probability)
        shock = float(forcing[i])

        stress = np.clip(
            0.87 * stress + 0.055 * active + 0.018 * max(circadian, 0)
            + 0.105 * shock - 0.035 * sleep + rng.normal(0, 0.018),
            0, 1,
        )
        recovery_debt = np.clip(
            0.95 * recovery_debt + 0.035 * active + 0.055 * stress
            + 0.045 * shock - 0.05 * sleep + rng.normal(0, 0.012),
            0, 1,
        )
        autonomic = np.clip(
            0.84 * autonomic + 0.11 * stress + 0.07 * recovery_debt
            + 0.11 * shock - 0.035 * sleep + rng.normal(0, 0.018),
            0, 1,
        )
        hemodynamic = np.clip(
            0.88 * hemodynamic + 0.085 * stress + 0.065 * recovery_debt
            + 0.13 * shock + rng.normal(0, 0.015),
            0, 1,
        )
        deterioration = np.clip(
            0.88 * deterioration + 0.08 * hemodynamic + 0.07 * autonomic
            + 0.06 * recovery_debt + 0.15 * shock - 0.055 * sleep
            + rng.normal(0, 0.012),
            0, 1,
        )

        activity_load = active * rng.uniform(0.65, 1.0)
        hr = (
            float(patient.baseline_hr)
            + 2.8 * circadian - 5.5 * sleep + 16 * activity_load
            + 12 * autonomic + 11 * deterioration + 4 * stress
            + rng.normal(0, 3.4)
        )
        hrv_baseline = np.clip(58 - 0.22 * (float(patient.age) - 45), 30, 62)
        hrv = (
            hrv_baseline + 7 * sleep - 13 * autonomic - 10 * deterioration
            - 7 * recovery_debt - 4 * stress + rng.normal(0, 5.5)
        )
        systolic = (
            float(patient.historical_systolic_bp)
            + 2.2 * circadian + 8 * activity_load + 10 * hemodynamic
            + 9 * deterioration + 3 * stress + rng.normal(0, 4.5)
        )
        diastolic = (
            float(patient.historical_diastolic_bp)
            + 1.0 * circadian + 4 * activity_load + 6 * hemodynamic
            + 4 * deterioration + rng.normal(0, 3.2)
        )
        steps = 0 if sleep else int(rng.poisson(2 if not active else 48 + 20 * activity_load))

        missing = int(rng.random() < config.dropout_probability * (1 + 0.9 * active))
        sensor_quality = float(np.clip(
            rng.normal(0.95 - 0.10 * active - 0.45 * missing, 0.055), 0, 1
        ))

        wearables.append({
            "timestamp": ts,
            "patient_id": patient.patient_id,
            "heart_rate_bpm": np.nan if missing else round(float(hr), 1),
            "hrv_ms": np.nan if missing else round(float(max(hrv, 10)), 1),
            "systolic_bp": np.nan if missing else round(float(systolic), 1),
            "diastolic_bp": np.nan if missing else round(float(diastolic), 1),
            "steps": steps,
            "activity_state": "sleep" if sleep else ("active" if active else "rest"),
            "sleep_state": sleep,
            "sensor_quality": round(sensor_quality, 3),
            "missing_data_indicator": missing,
        })
        latent.append({
            "timestamp": ts,
            "patient_id": patient.patient_id,
            "latent_stress": round(float(stress), 5),
            "latent_autonomic_instability": round(float(autonomic), 5),
            "latent_hemodynamic_load": round(float(hemodynamic), 5),
            "latent_recovery_debt": round(float(recovery_debt), 5),
            "latent_deterioration": round(float(deterioration), 5),
            "external_perturbation": round(shock, 5),
        })

    return pd.DataFrame(wearables), pd.DataFrame(latent)

def simulate_cohort(patients: pd.DataFrame, days: int = 3, seed: int = 43):
    rng = np.random.default_rng(seed)
    config = SimulationConfig(days=days)
    wearables = []
    latent = []
    for patient in patients.itertuples(index=False):
        wr, lt = simulate_patient(patient, config, rng)
        wearables.append(wr)
        latent.append(lt)
    return pd.concat(wearables, ignore_index=True), pd.concat(latent, ignore_index=True)
