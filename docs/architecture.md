# CardioTwin architecture

## Separation of concerns

CardioTwin now separates simulation truth, observable data, inference, twin state, and retrospective evaluation.

### 1. Hidden physiology simulator

data_generation/physiology.py evolves internal state variables that are not model inputs:

- stress
- autonomic instability
- hemodynamic load
- recovery debt
- deterioration state
- external perturbation

These variables are used only to produce synthetic observations and reference event truth.

### 2. Observation emission

The simulator emits noisy HR, HRV, systolic BP, diastolic BP, steps, activity, sleep, quality, and missingness.

The observation stream is the only physiological time-series input available to feature engineering and the live twin.

### 3. Event generation

data_generation/generate_events.py reads the hidden deterioration trajectory.

An event begins when latent deterioration remains at or above 0.72 for four consecutive five-minute steps. It ends after three consecutive steps below 0.48.

The 60-minute target is assigned before onset. Observed HR/BP values do not define the event.

### 4. Causal feature engineering

ml/preprocessing.py uses only static profile data and observations up to the current timestamp.

Features include short- and medium-window means, slopes, variability, activity, quality, freshness, and deviations from personal baselines.

The feature schema explicitly forbids latent state and event fields.

### 5. Model training

Patients are split before fitting.

Training:
- HistGradientBoostingClassifier
- class-balanced fitting
- active event periods excluded

Validation:
- Platt calibration
- alert threshold selection

Test:
- row metrics
- event detection and lead time
- false-alert episodes/patient-day
- patient-bootstrap confidence intervals
- ablation study

### 6. Digital twin

The digital twin does not read hidden physiology.

It combines:
- static profile
- replay clock
- current observed measurements
- causal features
- observable-state estimate
- calibrated forecast
- data-quality state
- SHAP contribution view
- forecast history
- scenario history

twin_engine/estimator.py provides an interpretable measurement-derived state estimate. This estimate is not the hidden simulator state.

### 7. Scenario engine

A scenario operates on a copy of recent observable history.

It generates twelve hypothetical five-minute observations, recomputes the entire feature pipeline after every generated point, and sends those features through the same saved model.

The original twin is not mutated.

### 8. Retrospective boundary

Live endpoints do not expose future event truth.

A separate retrospective endpoint exposes past/current event labels strictly for evaluation and debugging and is explicitly marked retrospective_evaluation_only.

## Data flow

    hidden physiology state
              |
              v
       observation emitter
              |
              v
       wearable-like stream ---------> retrospective event truth
              |                                |
              v                                |
       causal feature pipeline                 |
              |                                |
              v                                |
        calibrated model                       |
              |                                |
              v                                |
       observable twin state                   |
          /       |        \                   |
     forecast   SHAP      scenarios            |
          \       |        /                   |
              FastAPI                          |
                 |                             |
              React UI <---------------- evaluation workspace

The live inference path never consumes the right-hand retrospective truth path.
