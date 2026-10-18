# CardioTwin demo outline

## 1. Start with the problem, not the dashboard

Explain that the project asks whether observable synthetic physiology can anticipate a separate hidden deterioration process.

State the responsible-use boundary immediately.

## 2. Show the simulator separation

Open data_generation/physiology.py and generate_events.py.

Explain that hidden stress/autonomic/hemodynamic/recovery/deterioration states are simulation truth. HR/BP/HRV are noisy observations. The target comes from hidden deterioration, not an HR/BP threshold.

Show that sample_latent.csv is ignored by Git and not used by the model.

## 3. Show leakage controls

Open ml/preprocessing.py and models/feature_schema.json.

Show forbidden latent/event fields and causal rolling windows.

Explain why active-event periods are excluded from the early-warning classifier.

## 4. Show the evaluation honestly

Open the Evaluation workspace.

Discuss:
- ROC-AUC and patient-bootstrap CI
- PR-AUC versus low prevalence
- event detection
- lead time
- false-alert episodes per patient-day
- ablations

Point out that wearable-only ROC-AUC is currently higher than personalized fusion. Do not claim personalization always wins.

## 5. Show out-of-seed behavior

Show the three new synthetic cohorts and explain that this is a generator-seed stress test, not external validation.

## 6. Run the live twin

Select a patient and advance the clock.

Show:
- observed timeline
- personal baselines
- current forecast
- observable-state estimate
- state confidence
- SHAP contribution view

Explain that the live twin cannot access the hidden simulator state.

## 7. Run a scenario

Choose Recovery trajectory.

Show the twelve future observations/probabilities. Explain that rolling features are recomputed at every future step and the original twin remains unchanged.

Then compare with Sustained activity.

## 8. Show retrospective separation

Call or open the retrospective endpoint and point out that event truth is explicitly evaluation-only.

## 9. Close with limitations

Discuss synthetic physiology, alert burden, lack of clinical validation, absence of fairness/usability studies, and why the project should be treated as a research architecture rather than a medical product.
