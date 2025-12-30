import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app import models
from backend.app.database import get_db
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_users_table():
    # This fixture clears the users table before each test
    db: Session = next(get_db())
    db.query(models.User).delete()
    db.commit()
    yield
    db.query(models.User).delete()
    db.commit()

def create_user(email, full_name, password):
    db: Session = next(get_db())
    user = models.User(email=email, full_name=full_name, hashed_password=password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_register_with_valid_minimal_data():
    # Test Case 1
    payload = {
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "password": "StrongPass123!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["full_name"] == "Alice Smith"
    assert data["email"] == "alice@example.com"

def test_register_with_valid_data_and_file_uploads():
    # Test Case 2
    files = {
        "energy_source": ("energy.jpeg", io.BytesIO(b"jpegdata"), "image/jpeg"),
        "supporting_doc": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf"),
    }
    data = {
        "full_name": "Bob Lee",
        "email": "bob.lee@example.com",
        "password": "AnotherPass456!"
    }
    response = client.post("/api/auth/register", data=data, files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 2
    assert data["full_name"] == "Bob Lee"
    assert data["email"] == "bob.lee@example.com"

def test_register_and_skip_file_upload():
    # Test Case 3
    payload = {
        "full_name": "Carol White",
        "email": "carol.white@example.com",
        "password": "SkipUpload789!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 3
    assert data["full_name"] == "Carol White"
    assert data["email"] == "carol.white@example.com"
    assert data.get("dashboard_link") == "/dashboard"

def test_register_with_duplicate_email():
    # Test Case 4
    create_user("alice@example.com", "Alice Smith", "StrongPass123!")
    payload = {
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "password": "StrongPass123!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_register_with_invalid_email_format():
    # Test Case 5
    payload = {
        "full_name": "Dave Brown",
        "email": "not-an-email",
        "password": "ValidPass123!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid email format"}

def test_register_with_weak_password():
    # Test Case 6
    payload = {
        "full_name": "Eve Black",
        "email": "eve.black@example.com",
        "password": "123"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    assert response.json() == {"detail": "Password too weak"}

def test_register_with_missing_required_fields():
    # Test Case 7
    payload = {
        "email": "missing.name@example.com",
        "password": "ValidPass123!"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422
    assert response.json() == {"detail": "full_name is required"}

def test_register_with_invalid_file_type_upload():
    # Test Case 8
    files = {
        "energy_source": ("malware.exe", io.BytesIO(b"MZ..."), "application/x-msdownload"),
    }
    data = {
        "full_name": "Frank Green",
        "email": "frank.green@example.com",
        "password": "ValidPass123!"
    }
    response = client.post("/api/auth/register", data=data, files=files)
    assert response.status_code == 415
    assert response.json() == {"detail": "Unsupported file type"}

def test_register_with_file_exceeding_size_limit():
    # Test Case 9
    big_file = io.BytesIO(b"0" * (5 * 1024 * 1024 + 1))  # Just over 5MB
    files = {
        "supporting_doc": ("big.pdf", big_file, "application/pdf"),
    }
    data = {
        "full_name": "Grace Hall",
        "email": "grace.hall@example.com",
        "password": "ValidPass123!"
    }
    response = client.post("/api/auth/register", data=data, files=files)
    assert response.status_code == 413
    assert response.json() == {"detail": "File size exceeds 5MB limit"}

def test_register_endpoint_with_invalid_http_method():
    # Test Case 10
    response = client.get("/api/auth/register")
    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}

def test_register_with_file_exactly_at_5mb_limit():
    # Test Case 11
    exact_5mb = io.BytesIO(b"0" * (5 * 1024 * 1024))  # Exactly 5MB
    files = {
        "supporting_doc": ("doc.pdf", exact_5mb, "application/pdf"),
    }
    data = {
        "full_name": "Henry King",
        "email": "henry.king@example.com",
        "password": "ValidPass123!"
    }
    response = client.post("/api/auth/register", data=data, files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 4
    assert data["full_name"] == "Henry King"
    assert data["email"] == "henry.king@example.com"