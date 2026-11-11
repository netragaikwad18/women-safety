import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_full_user_and_sos_lifecycle():
    # 1. Register User
    reg_payload = {
        "full_name": "Integration Test Victim",
        "email": "integration_victim@test.com",
        "phone": "+919999988888",
        "password": "strongPassword123",
        "role": "user"
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    assert res_reg.status_code in [201, 400] # 201 or already exists in persistent test db

    # 2. Login
    res_login = client.post("/api/auth/login", json={
        "email": "integration_victim@test.com",
        "password": "strongPassword123"
    })
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]
    user_id = res_login.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Add Emergency Contact
    contact_payload = {
        "contact_name": "Father",
        "relationship_type": "Family",
        "phone_number": "+919845011111",
        "email": "father@example.com",
        "is_priority": True
    }
    res_contact = client.post("/api/contacts", json=contact_payload, headers=headers)
    assert res_contact.status_code == 201
    assert res_contact.json()["contact_name"] == "Father"

    # 4. Trigger Normal SOS Alert
    sos_payload = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "trigger_type": "button",
        "alert_mode": "normal",
        "location_address": "Bengaluru MG Road"
    }
    res_sos = client.post("/api/sos/trigger", json=sos_payload, headers=headers)
    assert res_sos.status_code == 201
    alert_id = res_sos.json()["id"]
    assert res_sos.json()["status"] == "active"

    # 5. Helper Register and Acknowledge Alert
    res_helper_reg = client.post("/api/auth/register", json={
        "full_name": "Community Rescuing Helper",
        "email": "helper_rescue@test.com",
        "phone": "+919877766655",
        "password": "helperPassword123",
        "role": "helper"
    })
    if res_helper_reg.status_code == 201:
        helper_token = res_helper_reg.json()["access_token"]
    else:
        helper_login = client.post("/api/auth/login", json={
            "email": "helper_rescue@test.com",
            "password": "helperPassword123"
        })
        helper_token = helper_login.json()["access_token"]

    helper_headers = {"Authorization": f"Bearer {helper_token}"}
    res_ack = client.post(f"/api/sos/{alert_id}/acknowledge", json={
        "eta_minutes": 5,
        "message": "Arriving on scooter with flashlights."
    }, headers=helper_headers)
    assert res_ack.status_code == 200
    assert res_ack.json()["eta_minutes"] == 5

    # 6. Resolve Alert
    res_resolve = client.put(f"/api/sos/{alert_id}/resolve", json={"notes": "Victim verified safe"}, headers=headers)
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "success"

def test_ai_risk_prediction_endpoint():
    res = client.post("/api/ai/predict-risk", json={
        "latitude": 12.9716,
        "longitude": 77.5946,
        "hour_of_day": 23,
        "speed_kmh": 4.5,
        "route_deviation_meters": 450.0,
        "battery_percentage": 9,
        "isolated_area": True
    })
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] in ["SAFE", "WARNING", "HIGH RISK"]
    assert "dataset_disclaimer" in data
    assert len(data["reasons"]) > 0

def test_safe_routes_recommendation():
    res = client.post("/api/routes/recommend", json={
        "origin_name": "Koramangala",
        "origin_lat": 12.9352,
        "origin_lng": 77.6245,
        "destination_name": "Indiranagar",
        "destination_lat": 12.9784,
        "destination_lng": 77.6408,
        "travel_mode": "walking"
    })
    assert res.status_code == 200
    data = res.json()
    assert "routes" in data
    assert len(data["routes"]) >= 2
    assert "nearby_emergency_services" in data

def test_bilingual_chatbot():
    # Test English
    res_en = client.post("/api/chatbot/query", json={"message": "I need emergency help!", "language": "en"})
    assert res_en.status_code == 200
    assert "112" in res_en.json()["response"]

    # Test Kannada
    res_kn = client.post("/api/chatbot/query", json={"message": "ನನಗೆ ತುರ್ತು ಸಹಾಯ ಬೇಕು", "language": "kn"})
    assert res_kn.status_code == 200
    assert "112" in res_kn.json()["response"]

def test_crime_hotspots_and_reporting():
    # List hotspots
    res_list = client.get("/api/hotspots")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1
