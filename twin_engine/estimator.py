from __future__ import annotations
import math

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-12.0, min(12.0, x))))

def estimate_observed_state(row) -> dict:
    """Estimate a compact state from observable features only.

    This is deliberately not the simulator's hidden latent state. It is an
    interpretable filtering layer that summarizes what the twin can infer from
    measurements available up to the current timestamp.
    """
    hr_load = float(row.hr_baseline_units)
    bp_load = float(row.sys_baseline_units)
    hr_trend = float(row.hr_slope_30) / 2.0
    bp_trend = float(row.sys_slope_30) / 2.0

    age_hrv_reference = max(30.0, min(62.0, 58.0 - 0.22 * (float(row.age) - 45.0)))
    hrv_deficit = (age_hrv_reference - float(row.hrv_mean_60)) / 10.0
    hrv_decline = max(0.0, -float(row.hrv_slope_30) / 2.0)

    cardiovascular_load = _sigmoid(-0.35 + 0.72 * hr_load + 0.64 * bp_load + 0.22 * hr_trend + 0.18 * bp_trend)
    autonomic_instability = _sigmoid(-0.55 + 0.70 * hrv_deficit + 0.35 * hrv_decline + 0.30 * max(hr_load, 0))
    recovery_debt = _sigmoid(
        -0.75 + 0.55 * hrv_deficit + 0.18 * float(row.steps_sum_60) / 100.0
        + 0.25 * (1 - float(row.sleep_state))
    )
    trajectory_instability = _sigmoid(
        -0.8 + 0.50 * abs(hr_trend) + 0.45 * abs(bp_trend)
        + 0.30 * float(row.hr_std_60) / 6.0 + 0.25 * float(row.sys_std_60) / 8.0
    )

    quality = max(0.0, min(1.0,
        0.55 * float(row.quality_mean_60)
        + 0.25 * (1.0 - float(row.missing_ratio_60))
        + 0.20 * math.exp(-float(row.time_since_valid_minutes) / 20.0)
    ))
    strain = (
        0.35 * cardiovascular_load
        + 0.28 * autonomic_instability
        + 0.20 * recovery_debt
        + 0.17 * trajectory_instability
    )
    return {
        "physiologic_strain": round(strain, 4),
        "cardiovascular_load": round(cardiovascular_load, 4),
        "autonomic_instability": round(autonomic_instability, 4),
        "recovery_debt": round(recovery_debt, 4),
        "trajectory_instability": round(trajectory_instability, 4),
        "confidence": round(quality, 4),
        "uncertainty": round(1.0 - quality, 4),
        "basis": "observable trailing-window state estimate; hidden simulator state is not used",
    }
