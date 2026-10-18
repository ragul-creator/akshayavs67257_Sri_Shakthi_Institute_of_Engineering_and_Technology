# CardioTwin demonstration video outline — 20+ minutes

## 0:00–2:00 — Problem and responsible-use boundary
Introduce the gap between occasional clinical snapshots and continuously changing physiology. State clearly that CardioTwin uses only synthetic data and forecasts a simulator-defined pattern, not heart attacks or diagnoses.

## 2:00–4:00 — Digital twin concept
Show the architecture and explain the persistent patient profile, replay clock, rolling physiology, personal baseline, current forecast, data quality, history, and scenario history.

## 4:00–7:00 — Synthetic data and event rule
Open sample_patients.csv and sample_wearables.csv. Explain 5-minute simulation cadence and the explicit assumption that blood pressure at this cadence is simulated. Show sample_events.csv. Explain the 12-hour reference baseline, +22 bpm HR threshold, +17 mmHg systolic threshold, 20-minute minimum duration, and 60-minute forecast label.

## 7:00–10:00 — Leakage-safe ML workflow
Show preprocessing.py and train.py. Explain patient-level 70/15/15 splitting, trailing rolling windows, absence of event-log features, logistic baseline, four ablations, gradient boosting, validation-only probability calibration, and validation-selected alert threshold.

## 10:00–12:00 — Genuine evaluation
Open the Model Evaluation screen. At the current reproducible seed, the personalized calibrated model has ROC-AUC about 0.833, PR-AUC about 0.339, F1 about 0.362, and Brier score about 0.026. Explain that exact metrics come from reports/evaluation_results.json and may change if simulation configuration or seeds change. Show the ablation table and robustness results. Explicitly discuss false alerts rather than presenting accuracy alone.

## 12:00–15:00 — Live digital twin replay
Select a patient. Show current HR, BP, baseline, data quality, and observation timestamp. Press Advance +5 min several times. Point out that charts and forecasts update from actual FastAPI responses and a saved model, not hardcoded UI values.

## 15:00–17:00 — Explainability
Show the top model-influence features and baseline deviations. Emphasize that feature influence is not causal or medical evidence.

## 17:00–19:00 — What-if simulation
Run Return toward baseline and Increased activity. Compare baseline and hypothetical model forecasts. State that the scenario works on a copied state and is not a treatment-effect estimate. Demonstrate that returning to the twin view leaves the original current state unchanged.

## 19:00–21:00 — Engineering quality and limitations
Show the tests, deterministic seeds, model metadata, SQLite audit database, API docs, and frontend production build. Discuss synthetic shortcuts, limited pilot scale, lack of clinical validation, and current explanation-method limitation.

## 21:00–22:00 — Future work and close
Scale to 500 patients and seven days, repeat across seeds, improve event simulator realism, add SHAP if deployment environment supports it, strengthen persistence/session support, and conduct domain-expert review before any clinical research use.
