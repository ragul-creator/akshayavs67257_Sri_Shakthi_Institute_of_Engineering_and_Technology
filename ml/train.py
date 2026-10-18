from __future__ import annotations
from pathlib import Path
import json
import sys
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (precision_score, recall_score, f1_score, roc_auc_score,
                             average_precision_score, confusion_matrix, brier_score_loss)
try:
    from ml.preprocessing import load_feature_frame, feature_groups
    from ml.calibration import calibrate_prefit
except ModuleNotFoundError:
    from preprocessing import load_feature_frame, feature_groups
    from calibration import calibrate_prefit

ROOT = Path(__file__).resolve().parents[1]

def split_patients(df, seed=2026):
    ids=np.array(sorted(df.patient_id.unique()))
    rng=np.random.default_rng(seed); rng.shuffle(ids)
    n=len(ids); n_train=int(.70*n); n_val=int(.15*n)
    return set(ids[:n_train]),set(ids[n_train:n_train+n_val]),set(ids[n_train+n_val:])

def metrics(y,prob,threshold=.5):
    pred=(prob>=threshold).astype(int)
    return {
        "precision":float(precision_score(y,pred,zero_division=0)),
        "recall":float(recall_score(y,pred,zero_division=0)),
        "f1":float(f1_score(y,pred,zero_division=0)),
        "roc_auc":float(roc_auc_score(y,prob)),
        "pr_auc":float(average_precision_score(y,prob)),
        "brier":float(brier_score_loss(y,prob)),
        "confusion_matrix":confusion_matrix(y,pred).tolist(),
    }

def best_threshold(y,prob):
    candidates=np.linspace(.05,.80,76)
    scores=[f1_score(y,(prob>=t).astype(int),zero_division=0) for t in candidates]
    return float(candidates[int(np.argmax(scores))])

def event_metrics(test_df,prob,threshold):
    x=test_df[["patient_id","timestamp","event_onset","target_60m"]].copy()
    x["alert"]=(prob>=threshold).astype(int)
    detected=0; leads=[]; total=0
    for _,g in x.groupby("patient_id"):
        g=g.sort_values("timestamp").reset_index(drop=True)
        for pos in np.flatnonzero(g["event_onset"].to_numpy()==1):
            total+=1; start=max(0,pos-12)
            alerts=np.flatnonzero(g.loc[start:pos-1,"alert"].to_numpy()==1)
            if len(alerts):
                detected+=1; first=start+int(alerts[0])
                leads.append(float((g.loc[pos,"timestamp"]-g.loc[first,"timestamp"]).total_seconds()/60))
    fp=int(((x["alert"]==1)&(x["target_60m"]==0)).sum())
    patient_days=max(1,x["patient_id"].nunique()*2)
    return {"event_detection_rate":detected/total if total else 0.0,
            "mean_early_warning_minutes":float(np.mean(leads)) if leads else 0.0,
            "false_alerts_per_patient_day":fp/patient_days,"test_events":total}

def main():
    df=load_feature_frame(ROOT)
    train_ids,val_ids,test_ids=split_patients(df)
    groups=feature_groups()
    train=df[df.patient_id.isin(train_ids)].dropna(subset=["target_60m"])
    val=df[df.patient_id.isin(val_ids)].dropna(subset=["target_60m"])
    test=df[df.patient_id.isin(test_ids)].dropna(subset=["target_60m"])
    ytr=train.target_60m.astype(int); yv=val.target_60m.astype(int); yt=test.target_60m.astype(int)

    baseline_features=["hr_mean_60","hr_std_60","hr_delta_30","sys_mean_60","sensor_quality"]
    baseline=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,class_weight="balanced",random_state=2026))
    baseline.fit(train[baseline_features],ytr)
    baseline_prob=baseline.predict_proba(test[baseline_features])[:,1]
    results={"baseline_logistic":metrics(yt,baseline_prob,.5),"ablations":{}}

    selected=None; selected_features=None; selected_threshold=.5
    for name,features in groups.items():
        raw=GradientBoostingClassifier(n_estimators=90,learning_rate=.06,max_depth=2,random_state=2026)
        raw.fit(train[features],ytr)
        model=calibrate_prefit(raw,val[features],yv)
        val_prob=model.predict_proba(val[features])[:,1]
        threshold=best_threshold(yv,val_prob)
        prob=model.predict_proba(test[features])[:,1]
        results["ablations"][name]=metrics(yt,prob,threshold)|{"threshold":threshold}
        if name=="personalized":
            selected=model; selected_features=features; selected_threshold=threshold
            results["selected_event_metrics"]=event_metrics(test,prob,threshold)

    joblib.dump(selected,ROOT/"models"/"cardio_twin_model.joblib")
    joblib.dump(baseline,ROOT/"models"/"baseline_model.joblib")
    schema={"features":selected_features,"feature_groups":groups,"baseline_features":baseline_features}
    (ROOT/"models"/"feature_schema.json").write_text(json.dumps(schema,indent=2))
    metadata={
        "model_version":"cardiotwin-gb-calibrated-0.2.0",
        "model_type":"GradientBoostingClassifier + Platt calibration",
        "probability_calibration":"Platt scaling fit on held-out validation patients",
        "threshold":selected_threshold,
        "threshold_policy":"F1-maximizing threshold selected on validation patients",
        "forecast_horizon_minutes":60,
        "train_patients":len(train_ids),"validation_patients":len(val_ids),"test_patients":len(test_ids),
        "python_version":sys.version.split()[0],"numpy_version":np.__version__,
        "pandas_version":pd.__version__,"scikit_learn_version":sklearn.__version__,
        "synthetic_data_only":True,"clinical_validation":False,
    }
    (ROOT/"models"/"model_metadata.json").write_text(json.dumps(metadata,indent=2))
    (ROOT/"reports"/"evaluation_results.json").write_text(json.dumps(results,indent=2))
    df.to_csv(ROOT/"data"/"features.csv",index=False)
    print(json.dumps({"threshold":selected_threshold,"test":results["ablations"]["personalized"],
                      "event":results["selected_event_metrics"]},indent=2))

if __name__=="__main__":
    main()
