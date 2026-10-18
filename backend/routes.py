from fastapi import APIRouter, HTTPException, Query

from backend.schemas import StepRequest, ResetRequest, ScenarioRequest
from twin_engine.state_manager import TwinEngine

router = APIRouter()
engine = TwinEngine()

def safe(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except KeyError:
        raise HTTPException(404, "Synthetic patient not found")
    except ValueError as exc:
        raise HTTPException(400, str(exc))

@router.get("/health")
def health():
    return {
        "status": "ok",
        "synthetic_only": True,
        "model_version": engine.metadata["model_version"],
        "event_source": engine.metadata.get("event_source"),
    }

@router.get("/patients")
def patients():
    rows = []
    for patient_id in engine.patient_ids():
        profile = engine.profile(patient_id)
        rows.append({
            "patient_id": patient_id,
            "age": int(profile["age"]),
            "sex": profile["sex"],
            "bmi": float(profile["bmi"]),
            "hypertension_history": bool(profile["hypertension_history"]),
            "diabetes_status": bool(profile["diabetes_status"]),
        })
    return rows

@router.get("/patients/{patient_id}")
def patient(patient_id: str):
    return safe(engine.profile, patient_id)

@router.get("/patients/{patient_id}/twin")
def twin(patient_id: str):
    return safe(engine.twin, patient_id)

@router.get("/patients/{patient_id}/forecast")
def forecast(patient_id: str):
    return safe(engine.forecast, patient_id)

@router.get("/patients/{patient_id}/observations")
def observations(patient_id: str, n: int = Query(72, ge=12, le=576)):
    return safe(engine.recent_observations, patient_id, n)

@router.get("/patients/{patient_id}/history")
def history(patient_id: str):
    safe(engine.profile, patient_id)
    return engine.histories.get(patient_id, [])

@router.get("/patients/{patient_id}/retrospective")
def retrospective(patient_id: str, n: int = Query(288, ge=12, le=864)):
    return safe(engine.retrospective, patient_id, n)

@router.post("/simulation/start")
def start(req: ResetRequest):
    return safe(engine.reset, req.patient_id)

@router.post("/simulation/reset")
def reset(req: ResetRequest):
    return safe(engine.reset, req.patient_id)

@router.post("/simulation/step")
def step(req: StepRequest):
    return safe(engine.step, req.patient_id, req.steps)

@router.post("/patients/{patient_id}/scenarios")
def scenario(patient_id: str, req: ScenarioRequest):
    return safe(engine.run_scenario, patient_id, req.scenario)

@router.get("/evaluation")
def evaluation():
    return engine.evaluation
