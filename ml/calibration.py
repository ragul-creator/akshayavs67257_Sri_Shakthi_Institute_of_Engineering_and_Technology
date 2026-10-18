from __future__ import annotations
import numpy as np
from sklearn.linear_model import LogisticRegression

def _logit(p):
    p=np.clip(np.asarray(p,dtype=float),1e-6,1-1e-6)
    return np.log(p/(1-p))

class CalibratedProbabilityModel:
    def __init__(self,base_model,calibrator):
        self.base_model=base_model
        self.calibrator=calibrator

    @property
    def feature_importances_(self):
        return self.base_model.feature_importances_

    def predict_proba(self,X):
        raw=self.base_model.predict_proba(X)[:,1]
        p=self.calibrator.predict_proba(_logit(raw).reshape(-1,1))[:,1]
        return np.column_stack([1-p,p])

def calibrate_prefit(base_model,X_validation,y_validation):
    raw=base_model.predict_proba(X_validation)[:,1]
    calibrator=LogisticRegression(max_iter=500,random_state=2026)
    calibrator.fit(_logit(raw).reshape(-1,1),y_validation)
    return CalibratedProbabilityModel(base_model,calibrator)
