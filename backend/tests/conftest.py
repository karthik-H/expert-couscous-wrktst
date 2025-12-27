import pytest
from starlette.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal

@pytest.fixture(scope="module")
def test_client():
    # Application dependency overrides could go here
    # For simplicity, we use the same SQLite DB file (or in-memory)
    # Re-creating tables for clean state might be better but let's stick to simple first
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    # Cleanup if needed
