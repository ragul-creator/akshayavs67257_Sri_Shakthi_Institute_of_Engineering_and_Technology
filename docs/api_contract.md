# CardioTwin API contract

Base URL: http://127.0.0.1:8000

## Live/replay endpoints

GET /health
Returns service status, model version, and event-source metadata.

GET /patients
Returns synthetic patient selector fields.

GET /patients/{patient_id}
Returns one static synthetic profile.

GET /patients/{patient_id}/observations?n=96
Returns observations up to the current replay clock.

GET /patients/{patient_id}/twin
Returns profile, replay state, current observations, observable-state estimate, calibrated forecast, explanation, forecast history, and scenario history.

GET /patients/{patient_id}/forecast
Returns the current 60-minute calibrated forecast.

GET /patients/{patient_id}/history
Returns forecast history created during replay.

POST /simulation/start
Body: {"patient_id":"P0001"}

POST /simulation/step
Body: {"patient_id":"P0001","steps":1}

POST /simulation/reset
Body: {"patient_id":"P0001"}

POST /patients/{patient_id}/scenarios
Body: {"scenario":"recovery"} or {"scenario":"sustained_activity"}

Scenario responses contain a twelve-step hypothetical probability trajectory.

## Retrospective endpoint

GET /patients/{patient_id}/retrospective?n=288

This endpoint is evaluation-only. It exposes past/current event labels and returns mode=retrospective_evaluation_only. It is not used by live inference.

## Evaluation endpoint

GET /evaluation

Returns:

- dataset/split description
- logistic baseline
- ablation results
- selected event metrics
- patient-bootstrap confidence intervals
- threshold operating curve
- calibration bins
- sensor robustness
- out-of-seed synthetic evaluation, when available

All outputs are synthetic research outputs and are not medical advice.
