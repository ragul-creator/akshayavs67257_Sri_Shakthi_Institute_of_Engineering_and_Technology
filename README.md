# CardioTwin

## Personalized Cardiovascular Digital Twin for 60-Minute Early Deterioration Forecasting

**Digital Twin Challenge 2026 — Healthcare Digital Twin Proof of Concept**

## Project Title

**CardioTwin — Personalized Cardiovascular Digital Twin for 60-Minute Early Deterioration Forecasting**

## Team Details

**Challenge team name:** `akshayavs67257`

| Name | Role |
|---|---|
| Akshaya V S | Team Leader |
| Kruthik Pranav TR | Team Member |
| Ragul S | Team Member |
| Sanjay S M | Team Member |

## College / Incubator Information

**Sri Shakthi Institute of Engineering and Technology, Coimbatore**

CardioTwin is a synthetic-data cardiovascular digital-twin research prototype that combines EHR-style patient history with wearable-style physiological time-series data to maintain an evolving patient-specific state and estimate whether a simulator-defined cardiovascular deterioration event will begin within the next **60 minutes**.

> **Responsible-use boundary:** CardioTwin is an educational/research prototype built on synthetic data. It is not clinically validated and must not be used for diagnosis, emergency triage, medication decisions, treatment selection, or real-patient risk prediction.

---

## Submission Requirements Covered

The following challenge deliverables are included directly in this public repository:

- [x] **Team Details**
- [x] **College / Incubator Information**
- [x] **Project Title**
- [x] **Problem Statement**
- [x] **Healthcare Use Case**
- [x] **Technical Stack**
- [x] **AI/ML Model and Framework Details**
- [x] **Open-Source License Details**
- [x] **Architecture Diagram in PDF format** — [View architecture.pdf](docs/architecture.pdf)
- [x] **Presentation in PDF format covering project details and outcomes** — [View presentation.pdf](docs/presentation.pdf)
- [x] **Publicly accessible repository and project files**

**Public repository:** https://github.com/ragul-creator/digital-twin

Additional technical documentation:

- [Architecture notes](docs/architecture.md)
- [Model card](docs/model_card.md)
- [API contract](docs/api_contract.md)
- [Demo walkthrough outline](docs/demo_video_outline.md)

---

## Problem Statement

Most conventional health monitoring is reactive: physiological measurements are reviewed after symptoms appear, thresholds are crossed, or a scheduled consultation occurs. Static population-level thresholds also do not capture how a patient's current physiology differs from their own baseline.

The Digital Twin Challenge asks teams to build a focused proof of concept rather than a whole-body digital twin. CardioTwin therefore focuses on one specific cardiovascular outcome:

> **Can an evolving patient-specific digital twin use longitudinal profile data and recent wearable-like physiology to estimate whether a synthetic cardiovascular deterioration event will begin within the next 60 minutes?**

The project is designed to explore four technical questions:

1. Can static EHR-style information and dynamic wearable data be fused without future-data leakage?
2. Can a patient-specific baseline improve the representation of current physiological state?
3. Can a model provide calibrated short-horizon forecasts rather than only binary labels?
4. Can the forecast be made interpretable, uncertainty-aware, and replayable as the patient's state evolves?

---

## Healthcare Use Case

CardioTwin models a **cardiovascular monitoring and early-warning research workflow**.

A synthetic patient has historical/profile information such as age, BMI, hypertension history, diabetes status, smoking history, baseline heart rate, and historical blood pressure. The same patient also produces a five-minute stream of wearable-like observations such as heart rate, heart-rate variability, blood pressure, steps, activity, sleep, sensor quality, and missingness.

As new observations arrive during replay, CardioTwin:

1. updates the patient's observable digital-twin state,
2. compares current physiology with that patient's own baseline,
3. computes leakage-safe short- and medium-window features,
4. evaluates data quality and measurement freshness,
5. runs the saved calibrated ML model,
6. estimates the probability of deterioration onset within 60 minutes,
7. explains the model score with SHAP,
8. stores forecast history, and
9. supports hypothetical 60-minute scenario trajectories.

This is a **research early-warning use case**, not a treatment recommendation system.

---

## Why This Is a Digital Twin

CardioTwin is more than a one-time classifier. Each synthetic patient has a persistent, evolving representation that changes as observations arrive.

The live twin contains:

- static patient profile,
- personal cardiovascular baselines,
- current wearable-like observations,
- recent physiological history,
- an estimated observable state,
- data-quality/confidence information,
- a calibrated 60-minute forecast,
- SHAP-based model explanations,
- forecast history,
- scenario history, and
- deterministic replay position.

The simulator's hidden physiological state is deliberately kept separate from the live twin. The twin must infer its observable state from measurements, rather than reading the simulator's ground truth.

---

## Specific Predicted Outcome

The supervised target is:

> **Probability that a simulator-defined hidden cardiovascular deterioration event begins within the next 60 minutes.**

The event is **not** defined directly from observed HR or BP thresholds.

Instead, the synthetic physiology simulator evolves an unobserved deterioration process. Event onset occurs when the hidden deterioration state remains above its configured onset threshold for a sustained period.

Current event definition:

- latent deterioration onset threshold: **0.72**
- sustained onset duration: **4 consecutive five-minute steps**
- event ends after **3 consecutive steps below 0.48**
- positive supervised window: **60 minutes before event onset**

Observed HR, HRV, BP, activity, or sensor-quality fields do not directly define the event.

---

## Data Used

### Static / EHR-Style Patient Information

CardioTwin uses synthetic profile/history fields such as:

- age,
- sex,
- BMI,
- hypertension history,
- diabetes status,
- smoking history,
- baseline heart rate,
- historical systolic blood pressure, and
- historical diastolic blood pressure.

### Dynamic / Wearable-Style Information

The five-minute observation stream contains:

- heart rate,
- heart-rate variability,
- systolic blood pressure,
- diastolic blood pressure,
- steps,
- activity state,
- sleep state,
- sensor quality, and
- missing-data indicators.

### Pilot Dataset

The current reproducible pilot contains:

| Item | Current pilot |
|---|---:|
| Synthetic patients | 120 |
| Simulated duration | 3 days/patient |
| Observation cadence | 5 minutes |
| Total observations | 103,680 |
| Hidden-state deterioration events | 271 |
| Positive pre-onset windows | ~3% |

A larger cohort generator is included for experiments such as **500 patients × 7 days**.

---

## Synthetic Physiology and Event Generation

The project separates **simulation truth** from **observable measurements**.

### Hidden simulator state

The simulator evolves internal variables including:

- physiological stress,
- autonomic instability,
- hemodynamic load,
- recovery debt,
- latent deterioration, and
- an unobserved external perturbation.

### Observable emission

Those hidden processes generate noisy measurements such as HR, HRV, BP, activity, sleep, and sensor quality.

The hidden latent stream can be generated for simulator validation, but it is not loaded by the live twin and is not part of the ML feature set.

This separation prevents the model from directly reading the variable that defines the target.

---

## Feature Engineering

All model features are causal: only the current observation and prior history are available.

### Static features

- age
- BMI
- hypertension history
- diabetes status
- smoking history

### Dynamic features

- current HR / HRV / BP
- pulse pressure
- 15-minute and 60-minute rolling means
- 15-minute and 30-minute slopes
- 60-minute variability
- recent activity and step load
- sleep state
- sensor quality
- recent missing-data ratio
- time since last valid measurement
- time-of-day encoding

### Personalized features

- HR deviation from personal baseline
- systolic BP deviation from personal baseline
- diastolic BP deviation from personal baseline
- relative HR
- normalized baseline-deviation units

### Leakage controls

The feature schema explicitly rejects fields such as:

- target labels,
- event-onset flags,
- event-active flags,
- latent deterioration,
- latent stress,
- latent autonomic state,
- latent hemodynamic state,
- recovery-debt ground truth,
- simulator perturbation fields, and
- future observations.

Active-event periods are also excluded from early-warning classifier training/evaluation because the target event has already begun.

---

## AI/ML Model and Framework Details

### Primary model

**scikit-learn HistGradientBoostingClassifier**

The current saved model version is:

`cardiotwin-hgb-latent-sim-0.3.0`

Model artifact:

`models/cardio_twin_model.joblib`

### Baseline model

A logistic-regression physiological baseline is also trained and saved as:

`models/baseline_model.joblib`

### Training protocol

The experiment uses a **patient-level split** of approximately:

- 70% training patients,
- 15% validation patients,
- 15% held-out test patients.

No synthetic patient appears in more than one split.

The training/evaluation pipeline includes:

1. causal feature engineering,
2. class-balanced model fitting,
3. Platt probability calibration on validation patients only,
4. prototype alert-threshold selection on validation patients only,
5. final evaluation on held-out patients,
6. patient-bootstrap confidence intervals,
7. ablation testing,
8. sensor-degradation robustness testing, and
9. out-of-seed synthetic cohort testing.

### Probability calibration

Raw tree-model scores are calibrated using **Platt scaling** fitted only on validation patients.

The dashboard therefore displays a calibrated model probability rather than an uncalibrated classifier score.

---

## Current Model Results

These results are from synthetic held-out patients and must not be interpreted as clinical performance.

| Metric | Held-out result |
|---|---:|
| ROC-AUC | **0.676** |
| ROC-AUC patient-bootstrap 95% CI | **0.630–0.723** |
| PR-AUC | **0.088** |
| F1 | **0.132** |
| Precision | **0.134** |
| Recall | **0.130** |
| Brier score | **0.038** |
| Events detected | **13 / 41** |
| Median lead time among detected events | **30 min** |
| False-alert burden | **2.87 episodes / patient-day** |

The project intentionally reports modest results rather than tuning the synthetic generator to create unrealistically perfect model performance.

---

## Ablation Study

The repository compares different information sources:

| Input set | ROC-AUC |
|---|---:|
| EHR/static only | 0.484 |
| Wearable only | 0.697 |
| EHR + wearable fusion | 0.664 |
| Personalized fusion | 0.676 |

The personalized model does not dominate every metric or every ablation. That result is reported directly rather than hidden.

---

## Out-of-Seed Synthetic Stress Test

The saved model is also evaluated **without refitting** on three newly generated synthetic cohorts that use different patient and physiology seeds.

Across the three cohorts:

| Metric | Mean ± seed-to-seed SD |
|---|---:|
| ROC-AUC | **0.748 ± 0.010** |
| PR-AUC | **0.163 ± 0.035** |
| F1 | **0.222 ± 0.040** |
| Event detection | **0.600 ± 0.057** |
| False alerts / patient-day | **3.27 ± 0.18** |

This measures sensitivity to generator seeds. It is **not external clinical validation**.

---

## Robustness Testing

CardioTwin evaluates model behavior under controlled degradation of observable inputs, including:

- additional sensor noise, and
- simulated loss of 15% of current readings.

Results are stored in:

`reports/evaluation_results.json`

These tests are useful for prototype robustness analysis but do not establish real-device reliability.

---

## Digital Twin State Estimation

The live twin does not expose the simulator's hidden state.

Instead, `twin_engine/estimator.py` derives an interpretable observable-state estimate from trailing measurements.

The dashboard tracks:

- cardiovascular load,
- autonomic instability,
- recovery debt,
- trajectory instability,
- composite physiological strain,
- confidence, and
- uncertainty.

This estimate summarizes what the twin can infer from available measurements. It is not a claim that hidden physiology has been recovered exactly.

---

## Explainability

CardioTwin uses **SHAP TreeExplainer** on the underlying gradient-boosting model.

For an individual prediction, the dashboard can show:

- contributing feature,
- current feature value,
- SHAP value,
- contribution direction, and
- explanation method.

SHAP values are interpreted as **model-score contributions**, not medical causality.

The displayed probability is subsequently calibrated, so SHAP explains the underlying tree-model score rather than the Platt calibration transformation.

---

## Scenario Engine

CardioTwin includes two current hypothetical trajectory scenarios:

- **Recovery trajectory**
- **Sustained activity trajectory**

A scenario does not edit final model features or directly alter the probability.

Instead it:

1. copies recent observable history,
2. generates twelve hypothetical five-minute observations,
3. recomputes the complete causal feature pipeline at every step,
4. sends each future state through the same saved calibrated model, and
5. returns a 60-minute probability trajectory.

The original patient replay state is not mutated.

Scenario outputs are phenomenological simulations and **must not be interpreted as treatment-effect estimates**.

---

## Technical Stack

| Layer | Technology |
|---|---|
| Programming language | Python 3.12, JavaScript |
| ML | scikit-learn |
| Explainability | SHAP |
| Data processing | Pandas, NumPy |
| Model serialization | Joblib |
| Backend API | FastAPI |
| API server | Uvicorn |
| Local audit storage | SQLite |
| Frontend | React |
| Frontend build tool | Vite |
| Charts | Recharts |
| Validation | Pydantic |
| Testing | Pytest |
| Version control | Git / GitHub |

---

## System Architecture

High-level flow:

```text
Synthetic patient profile
        │
        ├──────────────┐
        │              │
        ▼              ▼
Hidden physiology   Static EHR-style fields
simulator              │
        │              │
        ▼              │
Wearable-like          │
observations            │
        │              │
        └──────┬───────┘
               ▼
       Causal feature pipeline
               │
               ▼
      Calibrated ML forecast
               │
        ┌──────┼──────────┐
        ▼      ▼          ▼
 Twin state   SHAP    Data quality
        │
        ├───────────────┐
        ▼               ▼
 Scenario engine    Forecast history
        │               │
        └───────┬───────┘
                ▼
             FastAPI
                │
                ▼
        React research dashboard
```

A full architecture document is available here:

**[View Architecture Diagram PDF](docs/architecture.pdf)**

Supporting architecture notes:

**[Read Architecture Documentation](docs/architecture.md)**

---

## Dashboard Capabilities

The current React dashboard provides:

### Patient workspace

- synthetic patient list,
- patient-specific baselines,
- deterministic replay controls,
- current HR / BP / HRV,
- data-quality status,
- recent physiology timeline,
- baseline reference lines,
- calibrated 60-minute forecast,
- prototype alert threshold,
- forecast history,
- observable twin-state estimate,
- state confidence,
- SHAP model contributors.

### Scenario workspace

- recovery trajectory,
- sustained-activity trajectory,
- 12 future five-minute points,
- current / final / maximum probability comparison,
- explicit assumptions and non-causal warning.

### Evaluation workspace

- held-out model metrics,
- patient-bootstrap confidence intervals,
- ablation results,
- operating curve,
- event-level detection metrics,
- sensor robustness,
- out-of-seed synthetic evaluation.

---

## API

FastAPI exposes the main research workflows:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service/model status |
| GET | `/patients` | List synthetic patients |
| GET | `/patients/{id}` | Static patient profile |
| GET | `/patients/{id}/observations` | Recent observable physiology |
| GET | `/patients/{id}/twin` | Complete current twin state |
| GET | `/patients/{id}/forecast` | Current 60-minute forecast |
| GET | `/patients/{id}/history` | Forecast history |
| GET | `/patients/{id}/retrospective` | Explicit evaluation-only event truth |
| POST | `/simulation/start` | Initialize replay |
| POST | `/simulation/step` | Advance replay clock |
| POST | `/simulation/reset` | Reset replay |
| POST | `/patients/{id}/scenarios` | Run hypothetical trajectory |
| GET | `/evaluation` | Model/evaluation results |

Detailed contract:

**[View API Contract](docs/api_contract.md)**

---

## Repository Structure

```text
digital-twin/
├── backend/               # FastAPI routes, schemas, SQLite audit storage
├── data/                  # Synthetic sample profiles and observations
├── data_generation/       # Patient + hidden physiology simulation
├── docs/                  # Architecture, model card, API docs, presentation
├── frontend/              # React/Vite research dashboard
├── ml/                    # Features, training, calibration, evaluation, SHAP
├── models/                # Saved model artifacts and feature schema
├── reports/               # Generated evaluation results
├── scripts/               # End-to-end smoke test
├── tests/                 # Core and API tests
├── twin_engine/           # Replay, state estimation, scenario engine
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Quick Start

### Requirements

- Python 3.12+
- Node.js 20+
- npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/ragul-creator/digital-twin.git
cd digital-twin
```

### 2. Create a Python virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the API

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

API documentation:

`http://127.0.0.1:8000/docs`

### 4. Start the dashboard

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Dashboard:

`http://127.0.0.1:5173`

---

## Reproduce the Synthetic Experiment

Generate the pilot data:

```bash
python data_generation/build_sample.py
```

Train the model:

```bash
python -m ml.train
```

Run sensor robustness:

```bash
python -m ml.robustness
```

Run out-of-seed evaluation:

```bash
python -m ml.evaluate_multiseed
```

Generate a larger synthetic cohort:

```bash
python data_generation/generate_full.py --patients 500 --days 7 --seed 4200
```

---

## Testing

Run the automated test suite:

```bash
python -m pytest -q
```

Current verified status:

**13 tests passed**

Tests cover:

- deterministic patient generation,
- deterministic physiology generation,
- latent/observable stream separation,
- event construction,
- patient-level split isolation,
- feature-schema leakage protection,
- hidden-state isolation,
- scenario trajectory isolation,
- replay reset behavior,
- API prediction cycle,
- scenario API behavior,
- retrospective-mode labeling, and
- invalid-patient behavior.

End-to-end smoke test:

```bash
python scripts/smoke_test.py
```

---

## Suggested Judge / Demo Flow

A reviewer can understand the project quickly with this sequence:

1. **Select a synthetic patient** from the left-hand patient list.
2. **Inspect personal baselines and current vitals.**
3. **Advance the replay clock** by 5 or 30 minutes.
4. Watch the **physiology timeline and observable twin state** update.
5. Inspect the **60-minute calibrated forecast** and data-quality context.
6. Review the **SHAP contributors** for the current prediction.
7. Run a **Recovery** or **Sustained Activity** scenario.
8. Open **Evaluation** to inspect held-out metrics, ablations, robustness, and out-of-seed results.

---

## Presentation and Documentation

### Architecture

[**Architecture Diagram — PDF**](docs/architecture.pdf)

### Project Presentation

[**Project Presentation — PDF**](docs/presentation.pdf)

### Model Documentation

[**Model Card**](docs/model_card.md)

### API Documentation

[**API Contract**](docs/api_contract.md)

All of these files are stored in this public repository and are accessible without additional permissions.

---

## Open-Source License

CardioTwin is released under the **MIT License**.

[**View LICENSE**](LICENSE)

The MIT license permits use, copying, modification, distribution, and publication subject to the license terms.

---

## Known Limitations

CardioTwin is a proof-of-concept synthetic research system.

Current limitations include:

- fully synthetic training/evaluation data,
- phenomenological rather than clinically validated cardiovascular equations,
- hand-designed external perturbation process,
- synthetic calibration only,
- no real wearable or bedside-monitor integration,
- no real EHR/FHIR ingestion,
- no clinical validation,
- no prospective evaluation,
- no fairness study,
- no clinician usability study,
- non-production SQLite / in-memory replay infrastructure,
- no clinical authentication/RBAC workflow,
- alert burden that would be too high for real clinical deployment.

The system should therefore be evaluated as a **digital-twin architecture and ML research prototype**, not as a medical device or production clinical decision-support system.

---

## Responsible Use

CardioTwin uses synthetic data and is intended for education, research, hackathon demonstration, and digital-twin prototyping.

It must **not** be used to:

- diagnose cardiovascular disease,
- predict real heart attacks,
- triage emergencies,
- recommend medication,
- recommend treatment,
- estimate treatment effectiveness, or
- make decisions about real patients.

Scenario trajectories are hypothetical observation-space simulations, not causal treatment-effect estimates.

---

## Public Accessibility

This repository is public:

**https://github.com/ragul-creator/digital-twin**

The source code, README, architecture PDF, presentation PDF, model documentation, API documentation, license, tests, and supporting files are available directly from the repository without requesting additional repository permissions.
