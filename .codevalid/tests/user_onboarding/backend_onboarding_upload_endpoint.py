import io
import os
import tempfile
import shutil
import pytest

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app import models, database

from sqlalchemy.orm import Session

# --- Fixtures and Helpers ---

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function", autouse=True)
def db_session():
    # Use the actual DB for integration, or mock as needed
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def create_user(db: Session, user_id: int, onboarded=False):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.is_onboarded = onboarded
    else:
        user = models.User(id=user_id, username=f"user{user_id}", email=f"user{user_id}@test.com", is_onboarded=onboarded)
        db.add(user)
    db.commit()
    return user

def remove_onboarding_dir(user_id):
    dir_path = os.path.join("backend", "onboardingdoc", str(user_id))
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def make_image_file(filename="test.jpg", size=1024, content_type="image/jpeg"):
    return (filename, io.BytesIO(b"\xff\xd8\xff" + b"\x00" * (size - 3)), content_type)

def make_pdf_file(filename="test.pdf", size=1024):
    return (filename, io.BytesIO(b"%PDF-" + b"\x00" * (size - 5)), "application/pdf")

def make_docx_file(filename="test.docx", size=1024):
    return (filename, io.BytesIO(b"PK\x03\x04" + b"\x00" * (size - 4)), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

def make_txt_image_content(filename="test.txt", size=1024):
    # Content type is image/jpeg, extension is .txt
    return (filename, io.BytesIO(b"\xff\xd8\xff" + b"\x00" * (size - 3)), "image/jpeg")

# --- Test Cases ---

def setup_user_and_cleanup(db, user_id):
    create_user(db, user_id, onboarded=False)
    remove_onboarding_dir(user_id)

def teardown_user(db, user_id):
    db.query(models.User).filter(models.User.id == user_id).delete()
    db.commit()
    remove_onboarding_dir(user_id)

# Test Case 1: Successful onboarding with valid energy_pic and doc
def test_successful_onboarding_with_valid_energy_pic_and_doc(client, db_session):
    user_id = 10
    setup_user_and_cleanup(db_session, user_id)
    files = {
        "energy_pic": make_image_file(size=1024 * 100),  # 100KB
        "doc": make_pdf_file(size=1024 * 100),           # 100KB
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={
            "energy_pic": files["energy_pic"],
            "doc": files["doc"]
        }
    )
    assert response.status_code == 200
    assert response.json() == {"onboarding_complete": True}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert user.is_onboarded
    # Check files saved
    user_dir = os.path.join("backend", "onboardingdoc", str(user_id))
    assert os.path.exists(os.path.join(user_dir, "energy_source.jpeg"))
    assert os.path.exists(os.path.join(user_dir, "supporting_doc.pdf"))
    teardown_user(db_session, user_id)

# Test Case 2: Successful onboarding with no files (skip uploads)
def test_successful_onboarding_with_no_files(client, db_session):
    user_id = 11
    setup_user_and_cleanup(db_session, user_id)
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data
    )
    assert response.status_code == 200
    assert response.json() == {"onboarding_complete": True}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert user.is_onboarded
    teardown_user(db_session, user_id)

# Test Case 3: Reject non-image energy_pic
def test_reject_non_image_energy_pic(client, db_session):
    user_id = 12
    setup_user_and_cleanup(db_session, user_id)
    files = {
        "energy_pic": make_pdf_file(size=1024 * 100),  # PDF as energy_pic
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={"energy_pic": files["energy_pic"]}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "energy_pic must be an image"}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert not user.is_onboarded
    teardown_user(db_session, user_id)

# Test Case 4: Reject invalid doc file type
def test_reject_invalid_doc_file_type(client, db_session):
    user_id = 13
    setup_user_and_cleanup(db_session, user_id)
    files = {
        "doc": make_docx_file(size=1024 * 100),  # DOCX as doc
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={"doc": files["doc"]}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "doc must be PDF or image/jpeg/png"}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert not user.is_onboarded
    teardown_user(db_session, user_id)

# Test Case 5: Reject energy_pic over 5MB
def test_reject_energy_pic_over_5mb(client, db_session):
    user_id = 14
    setup_user_and_cleanup(db_session, user_id)
    files = {
        "energy_pic": make_image_file(size=5 * 1024 * 1024 + 1),  # 5MB + 1 byte
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={"energy_pic": files["energy_pic"]}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "energy_pic file size exceeds 5MB"}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert not user.is_onboarded
    teardown_user(db_session, user_id)

# Test Case 6: Reject doc over 5MB
def test_reject_doc_over_5mb(client, db_session):
    user_id = 15
    setup_user_and_cleanup(db_session, user_id)
    files = {
        "doc": make_pdf_file(size=5 * 1024 * 1024 + 1),  # 5MB + 1 byte
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={"doc": files["doc"]}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "doc file size exceeds 5MB"}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert not user.is_onboarded
    teardown_user(db_session, user_id)

# Test Case 7: Accept energy_pic at 5MB boundary
def test_accept_energy_pic_at_5mb_boundary(client, db_session):
    user_id = 16
    setup_user_and_cleanup(db_session, user_id)
    files = {
        "energy_pic": make_image_file(size=5 * 1024 * 1024),  # Exactly 5MB
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={"energy_pic": files["energy_pic"]}
    )
    assert response.status_code == 200
    assert response.json() == {"onboarding_complete": True}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert user.is_onboarded
    teardown_user(db_session, user_id)

# Test Case 8: Accept doc at 5MB boundary
def test_accept_doc_at_5mb_boundary(client, db_session):
    user_id = 17
    setup_user_and_cleanup(db_session, user_id)
    files = {
        "doc": make_pdf_file(size=5 * 1024 * 1024),  # Exactly 5MB
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={"doc": files["doc"]}
    )
    assert response.status_code == 200
    assert response.json() == {"onboarding_complete": True}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert user.is_onboarded
    teardown_user(db_session, user_id)

# Test Case 9: Reject missing userid
def test_reject_missing_userid(client, db_session):
    files = {
        "energy_pic": make_image_file(size=1024 * 100),
        "doc": make_pdf_file(size=1024 * 100),
    }
    response = client.post(
        "/api/onboarding/submit_onboarding",
        files={
            "energy_pic": files["energy_pic"],
            "doc": files["doc"]
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "userid is required"}

# Test Case 10: Reject invalid userid
def test_reject_invalid_userid(client, db_session):
    user_id = 99999
    files = {
        "energy_pic": make_image_file(size=1024 * 100),
        "doc": make_pdf_file(size=1024 * 100),
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={
            "energy_pic": files["energy_pic"],
            "doc": files["doc"]
        }
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

# Test Case 11: Successful onboarding with only energy_pic
def test_successful_onboarding_with_only_energy_pic(client, db_session):
    user_id = 18
    setup_user_and_cleanup(db_session, user_id)
    files = {
        "energy_pic": make_image_file(size=1024 * 100),
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={"energy_pic": files["energy_pic"]}
    )
    assert response.status_code == 200
    assert response.json() == {"onboarding_complete": True}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert user.is_onboarded
    teardown_user(db_session, user_id)

# Test Case 12: Successful onboarding with only doc
def test_successful_onboarding_with_only_doc(client, db_session):
    user_id = 19
    setup_user_and_cleanup(db_session, user_id)
    files = {
        "doc": make_pdf_file(size=1024 * 100),
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={"doc": files["doc"]}
    )
    assert response.status_code == 200
    assert response.json() == {"onboarding_complete": True}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert user.is_onboarded
    teardown_user(db_session, user_id)

# Test Case 13: Reject energy_pic with invalid extension (accept based on content type)
def test_accept_energy_pic_with_image_content_type_but_txt_extension(client, db_session):
    user_id = 20
    setup_user_and_cleanup(db_session, user_id)
    files = {
        "energy_pic": make_txt_image_content(filename="test.txt", size=1024 * 100),
    }
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data,
        files={"energy_pic": files["energy_pic"]}
    )
    assert response.status_code == 200
    assert response.json() == {"onboarding_complete": True}
    user = db_session.query(models.User).filter(models.User.id == user_id).first()
    assert user.is_onboarded
    teardown_user(db_session, user_id)

# Test Case 14: Dashboard access after skipping uploads
def test_dashboard_access_after_skipping_uploads(client, db_session):
    user_id = 21
    setup_user_and_cleanup(db_session, user_id)
    # Complete onboarding with no files
    data = {"userid": str(user_id)}
    response = client.post(
        "/api/onboarding/submit_onboarding",
        data=data
    )
    assert response.status_code == 200
    assert response.json() == {"onboarding_complete": True}
    # Simulate dashboard access
    dashboard_response = client.get("/dashboard")
    assert dashboard_response.status_code == 200
    # Accept either JSON or HTML dashboard, but check for access
    try:
        body = dashboard_response.json()
        assert body.get("dashboard_access") is True
    except Exception:
        # If HTML, check for dashboard keyword
        assert "dashboard" in dashboard_response.text.lower()
    teardown_user(db_session, user_id)