# CardioTwin

A synthetic cardiovascular digital-twin research prototype for short-horizon deterioration forecasting.

CardioTwin is not a clinical product. It does not diagnose cardiovascular disease, predict real heart attacks, recommend treatment, or estimate treatment effects.

## What changed in this version

The simulator and twin were rebuilt to remove the most artificial part of the earlier prototype.

The previous design injected abnormal HR/BP patterns and then defined the target from HR/BP thresholds. That made the prediction problem partly circular. The current design instead has two separate layers:

1. Hidden physiological simulation state: stress, autonomic instability, hemodynamic load, recovery debt, and a latent deterioration state evolve through time.
2. Observable measurements: HR, HRV, BP, activity, steps, sleep, missingness, and sensor quality are noisy emissions from that hidden process.

The event label is generated only from the hidden deterioration state. The ML pipeline never receives latent-state variables. That separation is enforced in code and tests.

## Research question

Given a synthetic patient's static profile and measurements available up to the current replay time, estimate the calibrated probability that a simulator-defined hidden deterioration event will begin within the next 60 minutes.

## Event process

data_generation/physiology.py evolves an unobserved state vector for each patient:

- latent stress
- latent autonomic instability
- latent hemodynamic load
- latent recovery debt
- latent deterioration
- an unobserved external perturbation

data_generation/generate_events.py defines onset from the hidden deterioration trajectory:

- onset threshold: latent deterioration >= 0.72
- required duration: 4 consecutive five-minute steps
- event ends after the state falls below 0.48 for 3 consecutive steps
- the supervised target is positive during the 60 minutes before onset

Observed HR or BP thresholds do not define the event.

Active-event rows are excluded from classifier training/evaluation because once onset has occurred they are not legitimate negative examples for an early-warning task.

## Pilot data

The reproducible pilot uses:

- 120 synthetic patients
- 3 simulated days per patient
- 103,680 five-minute observations
- 271 hidden-state deterioration events
- roughly 3% positive pre-onset windows

The hidden latent trajectory is written locally to data/sample_latent.csv for generator validation, but that file is ignored by Git and is never loaded by the model or live twin engine.

A larger cohort can be generated with:

    .\.venv\Scripts\python data_generation\generate_full.py --patients 500 --days 7 --seed 4200

## Observable feature pipeline

Features are causal: only current and preceding observations are used.

Static:
- age
- BMI
- hypertension history
- diabetes status
- smoking history

Dynamic:
- current HR, HRV, BP, pulse pressure
- 15- and 60-minute means
- 15- and 30-minute slopes
- 60-minute variability
- recent steps/activity/sleep
- sensor quality
- missing-data proportion
- time since a valid measurement
- time of day

Personalized:
- HR and BP deviation from generated profile baselines
- relative HR
- normalized baseline-deviation units

The schema explicitly rejects latent variables, event fields, and future labels.

## Model

The primary model is a HistGradientBoostingClassifier with class-balanced training. Platt probability calibration is fitted only on validation patients. The prototype alert threshold is selected only on validation patients.

The split is approximately 70/15/15 by patient. No patient is shared between train, validation, and test.

A logistic-regression physiological baseline is also trained.

## Current held-out results

These are synthetic benchmark results, not clinical evidence.

Selected personalized model on held-out patients:

- ROC-AUC: 0.676
- patient-bootstrap 95% CI: 0.630-0.723
- PR-AUC: 0.088
- F1: 0.132
- precision: 0.134
- recall: 0.130
- Brier score: 0.038
- 13 / 41 test events detected at the selected threshold
- median early-warning lead time among detected events: 30 minutes
- false-alert burden: 2.87 distinct false-alert episodes per simulated patient-day

The result is deliberately not optimized to look impressive.

### Ablation result

Current held-out ROC-AUC:

- EHR only: 0.484
- wearable only: 0.697
- EHR + wearable: 0.664
- personalized fusion: 0.676

Personalization does not dominate every ablation on this seed. It slightly improves PR-AUC relative to wearable-only but has lower ROC-AUC. That is reported as a result, not hidden.

## Out-of-seed synthetic stress test

The saved model is evaluated without refitting on three newly generated cohorts using different patient and physiology seeds.

Across those cohorts:

- mean ROC-AUC: 0.748 +/- 0.010
- mean PR-AUC: 0.163 +/- 0.035
- mean F1: 0.222 +/- 0.040
- mean event detection: 0.600 +/- 0.057
- mean false-alert burden: 3.27 +/- 0.18 episodes/patient-day

This checks sensitivity to generator seeds. It is not external validation.

## Measurement robustness

On the held-out cohort, controlled sensor noise and simulated loss of 15% of current readings did not materially change ranking performance in the current run. Results are saved in reports/evaluation_results.json.

This robustness test is narrow and does not establish real-device robustness.

## Digital twin state

The live twin does not expose the simulator's hidden state.

twin_engine/estimator.py produces an estimated observable state from trailing measurements:

- cardiovascular load
- autonomic instability
- recovery debt
- trajectory instability
- composite physiological strain
- confidence / uncertainty based on data quality and freshness

This is an interpretable filtering layer, not a claim that the true latent physiology has been recovered.

## Replay semantics

At each deterministic replay step the engine:

1. advances the patient clock
2. updates the observable state
3. uses causal rolling features
4. runs the saved calibrated model
5. computes a fresh SHAP explanation
6. records forecast history
7. stores an audit record in local SQLite

Retrospective event truth is available through a separate endpoint and is explicitly labeled evaluation-only.

## Explainability

SHAP TreeExplainer is run on the underlying gradient-boosting model.

The UI describes SHAP values as model-score contributions. They are not causal effects and they do not explain the subsequent calibration mapping.

## Scenario engine

Scenarios no longer edit ML features directly.

For each scenario, the engine:

1. copies recent observable history
2. generates twelve hypothetical future observations at five-minute intervals
3. applies explicit observation-space trajectory assumptions
4. recomputes all rolling features causally at each step
5. runs the same saved model for each future step
6. returns the full 60-minute probability trajectory

Current scenarios:

- recovery
- sustained_activity

These are phenomenological simulations, not treatment-effect models.

## Frontend

The React application is organized around analysis rather than KPI cards.

The Twin workspace contains:

- patient profile and baselines
- deterministic replay controls
- observed physiology timeline
- current calibrated forecast
- observable-state estimate and confidence
- SHAP contribution view
- 60-minute trajectory laboratory

The Evaluation workspace contains:

- held-out metrics with patient-bootstrap intervals
- ablation results
- alert operating curve
- measurement robustness
- out-of-seed synthetic stress-test results

## API

FastAPI routes include:

- GET /health
- GET /patients
- GET /patients/{id}
- GET /patients/{id}/observations
- GET /patients/{id}/twin
- GET /patients/{id}/forecast
- GET /patients/{id}/history
- GET /patients/{id}/retrospective
- POST /simulation/start
- POST /simulation/step
- POST /simulation/reset
- POST /patients/{id}/scenarios
- GET /evaluation

## Run

PowerShell:

    cd C:\Users\ragul\Desktop\CardioTwin
    .\.venv\Scripts\python data_generation\build_sample.py
    .\.venv\Scripts\python -m ml.train
    .\.venv\Scripts\python -m ml.robustness
    .\.venv\Scripts\python -m ml.evaluate_multiseed
    .\.venv\Scripts\python -m pytest -q
    .\.venv\Scripts\python scripts\smoke_test.py
    .\.venv\Scripts\python -m uvicorn backend.main:app --reload

Second terminal:

    cd C:\Users\ragul\Desktop\CardioTwin\frontend
    npm install
    npm run dev

Dashboard: http://127.0.0.1:5173

API docs: http://127.0.0.1:8000/docs

## Repository structure

    data_generation/
      physiology.py
      generate_patients.py
      generate_wearables.py
      generate_events.py
      build_sample.py
      generate_full.py

    ml/
      preprocessing.py
      calibration.py
      train.py
      robustness.py
      evaluate_multiseed.py
      explain.py

    twin_engine/
      estimator.py
      simulator.py
      scenarios.py
      state_manager.py

    backend/
      main.py
      routes.py
      schemas.py
      database.py

    frontend/src/
      components/
      services/
      App.jsx

    models/
    reports/
    tests/
    docs/

## Known limitations

This is still a synthetic-data project.

Important unresolved limitations:

- the physiology equations are phenomenological, not validated cardiovascular models
- the external perturbation process is hand-designed
- all patients eventually experience synthetic deterioration in the current pilot
- feature/model choices have not been exhaustively tuned
- calibration is evaluated only within synthetic distributions
- alert burden remains high for a real clinical workflow
- no fairness analysis has been completed
- no real sensor data has been used
- no clinician usability study has been performed
- local SQLite and in-memory replay state are demo infrastructure, not production healthcare architecture

Those limitations are part of the project, not footnotes to hide.

## Tests

Automated tests cover deterministic generation, latent/observable stream separation, event construction, patient-level split isolation, leakage protection, state-estimator separation, scenario trajectory isolation, replay reset, API prediction, retrospective labeling, and invalid patient behavior.

## Responsible use

CardioTwin is for educational/research demonstration on synthetic data only.

Do not use it for diagnosis, emergency triage, medication decisions, treatment selection, or real-patient risk prediction.
