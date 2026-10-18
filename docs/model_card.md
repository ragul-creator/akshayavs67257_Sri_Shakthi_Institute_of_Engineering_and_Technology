# CardioTwin model card

## Intended use
Educational research prototype for demonstrating a cardiovascular digital-twin workflow on fully synthetic data.

## Prediction target
A simulator-defined physiological deterioration event beginning within the next 60 minutes.

## Model
GradientBoostingClassifier using static EHR, dynamic trailing-window, and personal-baseline features. Raw model scores are Platt-calibrated on validation patients. The prototype alert threshold maximizes validation F1.

## Evaluation protocol
Patients are assigned to train, validation, and test groups at approximately 70/15/15. Test patients are never used for fitting, calibration, or threshold selection. Evaluation includes precision, recall, F1, ROC-AUC, PR-AUC, Brier score, confusion matrix, event detection rate, early-warning lead time, and false alerts per simulated patient-day.

## Limitations
Synthetic data can contain generator shortcuts and does not establish clinical utility. Event prevalence and physiology are controlled by simulation assumptions. Current feature explanations are labeled influence proxies, not causal explanations. The pilot is smaller than the intended full-scale generation target.

## Prohibited interpretation
Do not treat outputs as diagnoses, emergency predictions, medical triage, medication advice, or evidence that a hypothetical scenario would cause the same change in a real patient.
