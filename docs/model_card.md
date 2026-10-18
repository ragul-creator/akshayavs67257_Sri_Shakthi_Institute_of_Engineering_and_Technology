# CardioTwin model card

## Model version

cardiotwin-hgb-latent-sim-0.3.0

## Intended use

Synthetic-data research demonstration of patient-specific early-warning modeling and digital-twin replay.

## Target

Probability that a simulator-defined hidden deterioration event begins within 60 minutes.

The event is defined from a hidden simulator state, not from the model input variables.

## Inputs

Static profile fields plus causal observable time-series features derived from HR, HRV, BP, activity, sleep, steps, signal quality, missingness, and personal baselines.

No latent simulator variables, event logs, active-event flags, or future observations are model features.

## Training protocol

- patient-level train/validation/test split
- active-event periods excluded from the early-warning classifier
- HistGradientBoostingClassifier with balanced classes
- Platt calibration on validation patients
- threshold selection on validation patients only

## Current held-out performance

- ROC-AUC 0.676
- 95% patient-bootstrap interval 0.630-0.723
- PR-AUC 0.088
- F1 0.132
- precision 0.134
- recall 0.130
- Brier 0.038
- 13 of 41 test events detected
- median lead time 30 minutes among detected events
- 2.87 false-alert episodes per simulated patient-day

## Ablations

Wearable-only features currently have higher held-out ROC-AUC than the personalized fusion model. Personalization is therefore not claimed to dominate all alternatives.

## Out-of-seed stress test

Across three new synthetic cohorts without refitting:

- ROC-AUC mean 0.748, SD 0.010
- PR-AUC mean 0.163, SD 0.035
- event-detection mean 0.600, SD 0.057
- false-alert episodes/patient-day mean 3.27, SD 0.18

This is generator-seed robustness, not external validation.

## Explainability

SHAP TreeExplainer is used on the underlying tree model. SHAP values explain model score contribution, not causality and not the calibration mapping.

## Limitations

- fully synthetic data
- phenomenological simulator rather than validated cardiovascular equations
- hand-designed perturbation process
- no real-device validation
- no clinical validation
- no fairness study
- alert burden is not appropriate for real clinical deployment
- scenario outputs are not treatment-effect estimates

## Prohibited use

Do not use for diagnosis, triage, treatment selection, medication decisions, or real-patient risk prediction.
