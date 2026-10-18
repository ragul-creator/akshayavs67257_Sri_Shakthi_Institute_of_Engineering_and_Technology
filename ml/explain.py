from __future__ import annotations
import numpy as np
import pandas as pd

try:
    import shap
except ImportError:
    shap=None

FRIENDLY={
    "hr_deviation":"Heart-rate deviation from personal baseline",
    "sys_deviation":"Systolic BP deviation from personal baseline",
    "dia_deviation":"Diastolic BP deviation from personal baseline",
    "hr_mean_60":"60-minute mean heart rate",
    "hr_std_60":"60-minute heart-rate variability",
    "hr_delta_30":"30-minute heart-rate change",
    "sensor_quality":"Sensor quality",
    "missing_ratio_60":"Missing-data proportion",
}
_EXPLAINERS={}

def _shap_explanation(model,row,features,top_n):
    if shap is None:
        return None
    base=getattr(model,"base_model",model)
    key=id(base)
    if key not in _EXPLAINERS:
        _EXPLAINERS[key]=shap.TreeExplainer(base)
    X=pd.DataFrame([{f:float(row[f]) for f in features}])
    values=_EXPLAINERS[key].shap_values(X)
    if isinstance(values,list):
        values=values[-1]
    arr=np.asarray(values)
    if arr.ndim==3:
        arr=arr[:,:,1] if arr.shape[-1]>1 else arr[:,:,0]
    vals=arr.reshape(-1)[:len(features)]
    order=np.argsort(np.abs(vals))[::-1][:top_n]
    return [{
        "feature":features[i],
        "label":FRIENDLY.get(features[i],features[i].replace("_"," ").title()),
        "value":round(float(row[features[i]]),3),
        "shap_value":round(float(vals[i]),5),
        "direction":"raises model score" if vals[i]>=0 else "lowers model score",
        "method":"SHAP TreeExplainer on the underlying gradient-boosting model",
        "note":"Model contribution, not causal or medical evidence.",
    } for i in order]

def _fallback(model,row,features,top_n):
    imp=getattr(model,"feature_importances_",np.ones(len(features))/len(features))
    values=np.asarray([float(row[f]) for f in features])
    scale=np.nanstd(values)+1e-6
    score=np.asarray(imp)*(1+np.abs(values-np.nanmedian(values))/scale)
    order=np.argsort(score)[::-1][:top_n]
    return [{
        "feature":features[i],
        "label":FRIENDLY.get(features[i],features[i].replace("_"," ").title()),
        "value":round(float(values[i]),3),
        "importance_proxy":round(float(score[i]),5),
        "method":"fallback feature-influence proxy",
        "note":"Fallback model influence proxy; not causal or medical evidence.",
    } for i in order]

def explain_prediction(model,row,features,top_n=5):
    try:
        result=_shap_explanation(model,row,features,top_n)
        if result:
            return result
    except Exception:
        pass
    return _fallback(model,row,features,top_n)
