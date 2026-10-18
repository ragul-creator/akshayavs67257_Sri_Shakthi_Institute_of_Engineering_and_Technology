from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_and_prediction_cycle():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["event_source"] == "hidden latent deterioration state"

    patient_id = client.get("/patients").json()[0]["patient_id"]
    assert client.post("/simulation/start", json={"patient_id": patient_id}).status_code == 200

    response = client.post("/simulation/step", json={"patient_id": patient_id, "steps": 1})
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["forecast"]["event_probability"] <= 1
    assert body["synthetic"] is True
    assert "estimated_state" in body
    assert "physiologic_strain" in body["estimated_state"]

def test_scenario_returns_twelve_step_trajectory():
    patient_id = client.get("/patients").json()[0]["patient_id"]
    response = client.post(
        f"/patients/{patient_id}/scenarios",
        json={"scenario": "recovery"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["hypothetical"] is True
    assert len(result["trajectory"]) == 12

def test_retrospective_endpoint_is_explicitly_labeled():
    patient_id = client.get("/patients").json()[0]["patient_id"]
    response = client.get(f"/patients/{patient_id}/retrospective?n=24")
    assert response.status_code == 200
    assert response.json()["mode"] == "retrospective_evaluation_only"

def test_invalid_patient():
    assert client.get("/patients/NOT_REAL/twin").status_code == 404
