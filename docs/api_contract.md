# API contract

Base URL: http://127.0.0.1:8000

- GET /health — service and loaded model version.
- GET /patients — synthetic patient selector data.
- GET /patients/{patient_id} — static synthetic profile.
- GET /patients/{patient_id}/observations?n=36 — recent simulated observations.
- GET /patients/{patient_id}/twin — current virtual state, forecast, explanation, and replay state.
- GET /patients/{patient_id}/forecast — latest calibrated 60-minute forecast.
- GET /patients/{patient_id}/history — forecast history for the current replay session.
- POST /simulation/start — initialize a patient replay. JSON: {"patient_id":"P0001"}.
- POST /simulation/step — advance replay. JSON: {"patient_id":"P0001","steps":1}.
- POST /simulation/reset — reset replay. JSON: {"patient_id":"P0001"}.
- POST /patients/{patient_id}/scenarios — run isolated scenario. JSON: {"scenario":"return_toward_baseline"}.
- GET /evaluation — genuine saved held-out evaluation, ablations, calibration bins, and robustness results.

All predictions are synthetic-prototype outputs. Risk categories are prototype presentation categories, not medical triage instructions.
