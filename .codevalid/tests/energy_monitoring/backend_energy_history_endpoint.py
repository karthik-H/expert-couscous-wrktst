import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import EnergyData, User
from backend.app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import patch

client = TestClient(app)

@pytest.fixture
def db_session():
    # Provide a real or mock DB session depending on your test setup
    # Here, we assume get_db yields a Session
    db_gen = get_db()
    db = next(db_gen)
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def create_user(db: Session, onboarded=True, authenticated=True):
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password="fakehashed",
        onboarded=onboarded,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Simulate authentication (e.g., by returning a token or setting a cookie)
    # For simplicity, we assume dependency override or test client handles auth
    return user

def create_energy_records(db: Session, user_id: int, count: int):
    now = datetime(2025, 12, 26, 10, 0, 0)
    records = []
    for i in range(count):
        record = EnergyData(
            user_id=user_id,
            timestamp=now - timedelta(hours=i),
            energy=10.5 - i * 0.7
        )
        db.add(record)
        records.append(record)
    db.commit()
    return records

def authenticate_client(client, user):
    # Implement authentication for the test client (e.g., set headers/cookies)
    # This is a placeholder; adapt to your auth system
    client.headers.update({"Authorization": f"Bearer testtoken-{user.id}"})

@pytest.mark.usefixtures("db_session")
def test_get_energy_history_returns_last_100_records_for_onboarded_user(db_session):
    user = create_user(db_session, onboarded=True)
    create_energy_records(db_session, user.id, 120)
    authenticate_client(client, user)

    response = client.get("/api/energy/history")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 100
    # Check descending order
    timestamps = [r["timestamp"] for r in data]
    assert timestamps == sorted(timestamps, reverse=True)
    # Check first record is the latest
    assert data[0]["timestamp"] == "2025-12-26T10:00:00Z"
    assert data[0]["energy"] == 10.5

@pytest.mark.usefixtures("db_session")
def test_get_energy_history_returns_all_records_if_less_than_100(db_session):
    user = create_user(db_session, onboarded=True)
    create_energy_records(db_session, user.id, 1)
    authenticate_client(client, user)

    response = client.get("/api/energy/history")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["timestamp"] == "2025-12-26T10:00:00Z"
    assert data[0]["energy"] == 10.5

@pytest.mark.usefixtures("db_session")
def test_get_energy_history_fails_for_not_onboarded_user(db_session):
    user = create_user(db_session, onboarded=False)
    authenticate_client(client, user)

    response = client.get("/api/energy/history")
    assert response.status_code == 403
    assert response.json() == {"detail": "User not onboarded"}

def test_get_energy_history_fails_for_unauthenticated_user():
    # No authentication
    response = client.get("/api/energy/history")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.usefixtures("db_session")
def test_get_energy_history_returns_empty_list_if_no_data(db_session):
    user = create_user(db_session, onboarded=True)
    authenticate_client(client, user)

    response = client.get("/api/energy/history")
    assert response.status_code == 200
    assert response.json() == {"data": []}

@pytest.mark.usefixtures("db_session")
def test_get_energy_history_supports_custom_n_parameter(db_session):
    user = create_user(db_session, onboarded=True)
    create_energy_records(db_session, user.id, 20)
    authenticate_client(client, user)

    response = client.get("/api/energy/history?limit=10")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 10
    assert data[0]["timestamp"] == "2025-12-26T10:00:00Z"
    assert data[0]["energy"] == 10.5

@pytest.mark.usefixtures("db_session")
def test_get_energy_history_invalid_limit_parameter(db_session):
    user = create_user(db_session, onboarded=True)
    authenticate_client(client, user)

    response = client.get("/api/energy/history?limit=-5")
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid limit parameter"}

@pytest.mark.usefixtures("db_session")
def test_get_energy_history_post_method_not_allowed(db_session):
    user = create_user(db_session, onboarded=True)
    authenticate_client(client, user)

    response = client.post("/api/energy/history")
    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}