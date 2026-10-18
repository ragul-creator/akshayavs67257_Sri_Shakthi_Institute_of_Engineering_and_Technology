from fastapi.testclient import TestClient
from backend.main import app

client=TestClient(app)

def test_health_and_prediction_cycle():
    assert client.get("/health").status_code==200
    pid=client.get("/patients").json()[0]["patient_id"]
    assert client.post("/simulation/start",json={"patient_id":pid}).status_code==200
    r=client.post("/simulation/step",json={"patient_id":pid,"steps":1})
    assert r.status_code==200
    body=r.json()
    assert 0<=body["forecast"]["event_probability"]<=1
    assert body["synthetic"] is True

def test_invalid_patient():
    assert client.get("/patients/NOT_REAL/twin").status_code==404
