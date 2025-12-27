from starlette.testclient import TestClient

def test_read_root(test_client: TestClient):
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Energy Monitor API"}

def test_register_and_login(test_client: TestClient):
    # Register
    reg_payload = {
        "email": "test@example.com",
        "password": "strongpassword",
        "full_name": "Test User"
    }
    response = test_client.post("/api/auth/register", json=reg_payload)
    if response.status_code == 400:
        # User might already exist from previous runs
        pass
    else:
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    # Login
    login_data = {
        "username": "test@example.com",
        "password": "strongpassword"
    }
    response = test_client.post("/api/auth/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None

    # Get Me
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_energy_data_mock_fetch(test_client: TestClient):
    # Trigger scheduler manually or wait? 
    # Since it runs every minute, we might not want to wait in test.
    # Instead, we check if the endpoint returns data (might be 404 if no data yet)
    # Let's insert dummy data manually for test
    from app import models, database
    import datetime
    
    db = database.SessionLocal()
    data = models.EnergyData(
        generated_energy=50.5,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(data)
    db.commit()
    db.close()

    response = test_client.get("/api/energy/current")
    assert response.status_code == 200
    assert response.json()["generated_energy"] == 50.5
