# CardioTwin architecture

## Data flow

    Synthetic EHR generator
             |
             v
    Patient profiles -----------+
                                |
    Wearable simulator          |
             |                  |
             v                  v
    Rule-based event module -> leakage-safe feature engineering
                                |
                   +------------+-------------+
                   |                          |
             Baseline model          Fusion + personalization
                                              |
                                   validation calibration
                                              |
                              held-out patient evaluation
                                              |
                                  saved inference model
                                              |
    prerecorded observations -> deterministic replay clock
                                              |
                                      digital twin state
                                      /      |        \
                               forecast  explanation  scenario copy
                                      \      |        /
                                           FastAPI
                                             |
                                  SQLite audit persistence
                                             |
                                  React / Recharts dashboard

## Component responsibilities

- data_generation: deterministic synthetic profiles, wearable observations, explicit event derivation, labels, and validation.
- ml: trailing-window feature engineering, patient-level split, baseline and ablation training, probability calibration, evaluation, and robustness checks.
- twin_engine: deterministic replay cursor, evolving patient state, forecast history, and isolated hypothetical scenarios.
- backend: validated FastAPI contract, CORS configuration, and SQLite audit logging.
- frontend: patient selection, current twin state, trends, calibrated forecast, model explanations, scenario comparison, ablation metrics, and disclaimers.

## Leakage controls

1. Patients are split before model fitting; no patient appears in more than one split.
2. Rolling features use the current and preceding observations only.
3. Missing values use patient-forward-fill or declared static baselines; no backward-fill is used.
4. Event logs, event-active flags, hidden simulator episode flags, and future labels are excluded from model features.
5. The validation group is used for calibration and alert-threshold selection; final metrics are reported on held-out test patients.

## Event definition

Personal reference baselines are the median valid heart rate and systolic blood pressure over the first 12 simulated hours. A synthetic deterioration event is a contiguous run of at least four five-minute observations (20 minutes) in which heart rate is at least 22 bpm above that reference and systolic pressure is at least 17 mmHg above it. The event starts at the first qualifying observation and ends at the last consecutive qualifying observation. The generator spaces injected episodes apart; any naturally contiguous qualifying readings are treated as one event. The forecast target is 1 for non-event observations in the 60 minutes before onset.

This is a simulator-defined pattern and is not a clinically validated endpoint.
