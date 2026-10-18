from pydantic import BaseModel, Field

class StepRequest(BaseModel):
    patient_id: str
    steps: int = Field(default=1, ge=1, le=24)

class ResetRequest(BaseModel):
    patient_id: str

class ScenarioRequest(BaseModel):
    scenario: str
