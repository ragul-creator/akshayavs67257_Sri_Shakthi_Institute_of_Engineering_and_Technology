from __future__ import annotations

from pathlib import Path
import json
import sys
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix, brier_score_loss,
)
from sklearn.calibration import calibration_curve

try:
    from ml.preprocessing import load_feature_frame, feature_groups, assert_no_leakage
    from ml.calibration import calibrate_prefit
except ModuleNotFoundError:
    from preprocessing import load_feature_frame, feature_groups, assert_no_leakage
    from calibration import calibrate_prefit

ROOT = Path(__file__).resolve().parents[1]
SPLIT_SEED = 2026

def split_patients(df: pd.DataFrame, seed: int = SPLIT_SEED):
    ids = np.array(sorted(df.patient_id.unique()))
    rng = np.random.default_rng(seed)
    rng.shuffle(ids)
    n = len(ids)
    n_train = int(0.70 * n)
    n_val = int(0.15 * n)
    return set(ids[:n_train]), set(ids[n_train:n_train+n_val]), set(ids[n_train+n_val:])

def metrics(y, prob, threshold=0.5):
    y = np.asarray(y, dtype=int)
    prob = np.asarray(prob, dtype=float)
    pred = (prob >= threshold).astype(int)
    return {
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, prob)),
        "pr_auc": float(average_precision_score(y, prob)),
        "brier": float(brier_score_loss(y, prob)),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
    }

def best_threshold(y, prob):
    candidates = np.linspace(0.03, 0.65, 125)
    scores = np.array([f1_score(y, prob >= t, zero_division=0) for t in candidates])
    return float(candidates[int(np.argmax(scores))])

def patient_days(frame: pd.DataFrame) -> float:
    total = 0.0
    for _, group in frame.groupby("patient_id"):
        span = (group["timestamp"].max() - group["timestamp"].min()).total_seconds() / 86400
        total += max(span + 5 / 1440, 5 / 1440)
    return max(total, 1.0)

def event_metrics(full_test, full_prob, threshold):
    x = full_test[["patient_id", "timestamp", "event_onset", "event_active", "target_60m"]].copy()
    x["probability"] = np.asarray(full_prob)
    x["alert"] = x["probability"] >= threshold

    detected = 0
    leads = []
    total = 0
    for _, group in x.groupby("patient_id"):
        group = group.sort_values("timestamp").reset_index(drop=True)
        for pos in np.flatnonzero(group["event_onset"].to_numpy() == 1):
            total += 1
            start = max(0, pos - 12)
            eligible = group.loc[start:pos-1]
            alerts = eligible.index[(eligible["alert"]) & (eligible["event_active"] == 0)].to_numpy()
            if len(alerts):
                detected += 1
                first = int(alerts[0])
                leads.append(float(
                    (group.loc[pos, "timestamp"] - group.loc[first, "timestamp"]).total_seconds() / 60
                ))

    false_alert_episodes = 0
    for _, group in x.groupby("patient_id"):
        group = group.sort_values("timestamp").reset_index(drop=True)
        alert = group["alert"].to_numpy(dtype=bool)
        starts = np.flatnonzero(alert & np.r_[True, ~alert[:-1]])
        for start in starts:
            end = int(start)
            while end + 1 < len(group) and alert[end + 1]:
                end += 1
            run = group.iloc[int(start):end + 1]
            overlaps_true_window = bool((run["target_60m"] == 1).any() or (run["event_active"] == 1).any())
            if not overlaps_true_window:
                false_alert_episodes += 1

    return {
        "event_detection_rate": detected / total if total else 0.0,
        "detected_events": detected,
        "test_events": total,
        "mean_early_warning_minutes": float(np.mean(leads)) if leads else 0.0,
        "median_early_warning_minutes": float(np.median(leads)) if leads else 0.0,
        "false_alerts_per_patient_day": false_alert_episodes / patient_days(x),
    }

def bootstrap_intervals(test_eval, prob, threshold, repeats=250, seed=77):
    rng = np.random.default_rng(seed)
    ids = np.array(sorted(test_eval.patient_id.unique()))
    values = {k: [] for k in ["roc_auc", "pr_auc", "f1", "precision", "recall", "brier"]}
    prob_series = pd.Series(np.asarray(prob), index=test_eval.index)
    for _ in range(repeats):
        sampled = rng.choice(ids, size=len(ids), replace=True)
        y_parts, p_parts = [], []
        for pid in sampled:
            mask = test_eval.patient_id == pid
            y_parts.append(test_eval.loc[mask, "target_60m"].astype(int).to_numpy())
            p_parts.append(prob_series.loc[mask].to_numpy())
        y = np.concatenate(y_parts)
        p = np.concatenate(p_parts)
        if len(np.unique(y)) < 2:
            continue
        m = metrics(y, p, threshold)
        for key in values:
            values[key].append(m[key])
    return {
        key: {
            "low_95": float(np.quantile(vals, 0.025)),
            "high_95": float(np.quantile(vals, 0.975)),
        }
        for key, vals in values.items() if vals
    }

def operating_curve(test_eval, eval_prob, full_test, full_prob):
    points = []
    for threshold in np.linspace(0.04, 0.50, 24):
        row_metrics = metrics(test_eval.target_60m.astype(int), eval_prob, float(threshold))
        event = event_metrics(full_test, full_prob, float(threshold))
        points.append({
            "threshold": round(float(threshold), 3),
            "precision": row_metrics["precision"],
            "recall": row_metrics["recall"],
            "f1": row_metrics["f1"],
            "event_detection_rate": event["event_detection_rate"],
            "false_alerts_per_patient_day": event["false_alerts_per_patient_day"],
        })
    return points

def new_primary_model():
    return HistGradientBoostingClassifier(
        learning_rate=0.055,
        max_iter=200,
        max_leaf_nodes=15,
        min_samples_leaf=30,
        l2_regularization=0.7,
        class_weight="balanced",
        random_state=SPLIT_SEED,
    )

def main():
    df = load_feature_frame(ROOT)
    train_ids, val_ids, test_ids = split_patients(df)
    groups = feature_groups()

    train_all = df[df.patient_id.isin(train_ids)].copy()
    val_all = df[df.patient_id.isin(val_ids)].copy()
    test_all = df[df.patient_id.isin(test_ids)].copy()

    # Early-warning classifier is evaluated only before onset or during ordinary periods.
    # Active-event rows are not legitimate negatives once the target event has begun.
    train = train_all[train_all.event_active == 0].copy()
    val = val_all[val_all.event_active == 0].copy()
    test_eval = test_all[test_all.event_active == 0].copy()
    ytr = train.target_60m.astype(int)
    yv = val.target_60m.astype(int)
    yt = test_eval.target_60m.astype(int)

    baseline_features = [
        "hr_mean_15", "hr_mean_60", "hr_std_60", "hr_slope_15", "hr_slope_30",
        "hrv_mean_15", "hrv_mean_60", "sys_mean_15", "sys_mean_60", "sensor_quality",
    ]
    baseline = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1500, class_weight="balanced", random_state=SPLIT_SEED),
    )
    baseline.fit(train[baseline_features], ytr)
    baseline_prob = baseline.predict_proba(test_eval[baseline_features])[:, 1]

    results = {
        "dataset": {
            "patients": int(df.patient_id.nunique()),
            "rows": int(len(df)),
            "eligible_rows": int((df.event_active == 0).sum()),
            "eligible_positive_rate": float(df.loc[df.event_active == 0, "target_60m"].mean()),
            "train_patients": len(train_ids),
            "validation_patients": len(val_ids),
            "test_patients": len(test_ids),
            "split_seed": SPLIT_SEED,
            "active_event_rows_excluded_from_classifier": True,
        },
        "baseline_logistic": metrics(yt, baseline_prob, 0.5),
        "ablations": {},
    }

    selected = None
    selected_features = None
    selected_threshold = None
    selected_eval_prob = None
    selected_full_prob = None

    for name, features in groups.items():
        assert_no_leakage(features)
        raw = new_primary_model()
        raw.fit(train[features], ytr)
        calibrated = calibrate_prefit(raw, val[features], yv)
        val_prob = calibrated.predict_proba(val[features])[:, 1]
        threshold = best_threshold(yv.to_numpy(), val_prob)
        eval_prob = calibrated.predict_proba(test_eval[features])[:, 1]
        results["ablations"][name] = metrics(yt, eval_prob, threshold) | {
            "threshold": threshold,
            "feature_count": len(features),
        }
        if name == "personalized":
            selected = calibrated
            selected_features = features
            selected_threshold = threshold
            selected_eval_prob = eval_prob
            selected_full_prob = calibrated.predict_proba(test_all[features])[:, 1]

    results["selected_event_metrics"] = event_metrics(test_all, selected_full_prob, selected_threshold)
    results["bootstrap_95_ci"] = bootstrap_intervals(
        test_eval, selected_eval_prob, selected_threshold
    )
    results["operating_curve"] = operating_curve(
        test_eval, selected_eval_prob, test_all, selected_full_prob
    )

    observed, predicted = calibration_curve(
        yt, selected_eval_prob, n_bins=10, strategy="quantile"
    )
    results["calibration_bins"] = [
        {"mean_predicted": float(p), "observed_fraction": float(o)}
        for p, o in zip(predicted, observed)
    ]

    joblib.dump(selected, ROOT/"models"/"cardio_twin_model.joblib")
    joblib.dump(baseline, ROOT/"models"/"baseline_model.joblib")

    schema = {
        "features": selected_features,
        "feature_groups": groups,
        "baseline_features": baseline_features,
        "forbidden_fields": sorted([
            "target_60m", "event_onset", "event_active",
            "latent_deterioration", "latent_stress",
            "latent_autonomic_instability", "latent_hemodynamic_load",
            "latent_recovery_debt", "external_perturbation",
        ]),
    }
    (ROOT/"models"/"feature_schema.json").write_text(json.dumps(schema, indent=2))

    metadata = {
        "model_version": "cardiotwin-hgb-latent-sim-0.3.0",
        "model_type": "HistGradientBoostingClassifier + Platt calibration",
        "probability_calibration": "Platt scaling fit on held-out validation patients",
        "threshold": selected_threshold,
        "threshold_policy": "F1-maximizing threshold selected on validation patients",
        "forecast_horizon_minutes": 60,
        "event_source": "hidden latent deterioration state",
        "active_event_rows_excluded_from_classifier": True,
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "scikit_learn_version": sklearn.__version__,
        "synthetic_data_only": True,
        "clinical_validation": False,
    }
    (ROOT/"models"/"model_metadata.json").write_text(json.dumps(metadata, indent=2))
    (ROOT/"reports"/"evaluation_results.json").write_text(json.dumps(results, indent=2))

    predictions = test_all[[
        "patient_id", "timestamp", "target_60m", "event_onset", "event_active"
    ]].copy()
    predictions["probability"] = selected_full_prob
    predictions["alert"] = selected_full_prob >= selected_threshold
    predictions.to_csv(ROOT/"reports"/"test_predictions.csv", index=False)

    df.to_csv(ROOT/"data"/"features.csv", index=False)
    print(json.dumps({
        "model_version": metadata["model_version"],
        "threshold": selected_threshold,
        "test": results["ablations"]["personalized"],
        "event": results["selected_event_metrics"],
        "ci": results["bootstrap_95_ci"],
    }, indent=2))

if __name__ == "__main__":
    main()
