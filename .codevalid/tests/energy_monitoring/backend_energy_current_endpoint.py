import pytest
from datetime import datetime, timedelta
from fastapi import status
from jose import jwt

from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import User, EnergyData
from app.api.auth import SECRET_KEY, ALGORITHM
from starlette.testclient import TestClient

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    # Setup: create tables and clear data
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(EnergyData).delete()
    db.query(User).delete()
    db.commit()
    yield
    db.close()
    # Teardown: drop all data (keep tables for speed)
    db = SessionLocal()
    db.query(EnergyData).delete()
    db.query(User).delete()
    db.commit()
    db.close()

@pytest.fixture
def client():
    return TestClient(app)

def create_user(db, email="user@example.com", onboarded=True, password_hash="fakehash"):
    user = User(
        email=email,
        full_name="Test User",
        hashed_password=password_hash,
        is_active=True,
        is_onboarded=onboarded
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_energy_data(db, user, energy, timestamp):
    data = EnergyData(
        generated_energy=energy,
        timestamp=timestamp,
        user_id=user.id
    )
    db.add(data)
    db.commit()
    db.refresh(data)
    return data

def get_token_for_user(user):
    payload = {"sub": user.email}
    expire = datetime.utcnow() + timedelta(minutes=30)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Test Case 1
def test_get_current_energy_returns_latest_record(client):
    db = SessionLocal()
    user = create_user(db, onboarded=True)
    # Create two records, latest has higher timestamp
    t1 = datetime(2025, 12, 27, 6, 0, 0)
    t2 = datetime(2025, 12, 27, 7, 0, 0)
    create_energy_data(db, user, 50.0, t1)
    create_energy_data(db, user, 123.45, t2)
    token = get_token_for_user(user)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/energy/current", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["generated_energy"] == 123.45
    assert data["timestamp"].startswith("2025-12-27T07:00:00")

# Test Case 2
def test_get_current_energy_raises_403_if_not_onboarded(client):
    db = SessionLocal()
    user = create_user(db, onboarded=False)
    token = get_token_for_user(user)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/energy/current", headers=headers)
    assert response.status_code == 403
    assert "onboard" in response.json()["detail"].lower()

# Test Case 3
def test_get_current_energy_raises_404_if_no_records(client):
    db = SessionLocal()
    user = create_user(db, onboarded=True)
    token = get_token_for_user(user)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/energy/current", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "No energy data found"

# Test Case 4
def test_get_current_energy_raises_401_if_unauthenticated(client):
    response = client.get("/api/energy/current")
    assert response.status_code == 401
    # Accept either error message depending on FastAPI/JWT error
    assert "not authenticated" in response.json()["detail"].lower() or "credentials" in response.json()["detail"].lower()

# Test Case 5
def test_get_current_energy_raises_405_on_post(client):
    db = SessionLocal()
    user = create_user(db, onboarded=True)
    token = get_token_for_user(user)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/energy/current", headers=headers)
    assert response.status_code == 405
    assert "method" in response.json()["detail"].lower()

# Test Case 6
def test_get_current_energy_returns_single_record(client):
    db = SessionLocal()
    user = create_user(db, onboarded=True)
    t1 = datetime(2025, 12, 27, 6, 0, 0)
    create_energy_data(db, user, 50.0, t1)
    token = get_token_for_user(user)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/energy/current", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["generated_energy"] == 50.0
    assert data["timestamp"].startswith("2025-12-27T06:00:00")

# Test Case 7
def test_get_current_energy_raises_401_invalid_token(client):
    db = SessionLocal()
    user = create_user(db, onboarded=True)
    # Use an invalid token
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/api/energy/current", headers=headers)
    assert response.status_code == 401
    # Accept either error message depending on FastAPI/JWT error
    assert "credentials" in response.json()["detail"].lower() or "not authenticated" in response.json()["detail"].lower()