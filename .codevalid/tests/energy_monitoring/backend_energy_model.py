import pytest
import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.models import Base, User, EnergyData
from backend.app.database import engine, SessionLocal

@pytest.fixture(scope="function")
def db():
    # Setup: create tables and yield a session
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def user(db):
    u = User(email="testuser@example.com", full_name="Test User", hashed_password="hashed", is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def test_create_energydata_with_valid_fields(db, user):
    """Test Case 1: Create EnergyData with valid fields"""
    now = datetime.datetime.utcnow()
    energy = EnergyData(timestamp=now, generated_energy=123.45, user_id=user.id)
    db.add(energy)
    db.commit()
    db.refresh(energy)
    fetched = db.query(EnergyData).filter_by(id=energy.id).first()
    assert fetched is not None
    assert fetched.timestamp == now
    assert fetched.generated_energy == 123.45
    assert fetched.user_id == user.id

def test_create_energydata_without_user_id(db):
    """Test Case 2: Create EnergyData without user_id"""
    now = datetime.datetime.utcnow()
    energy = EnergyData(timestamp=now, generated_energy=50.0)
    db.add(energy)
    db.commit()
    db.refresh(energy)
    assert energy.user_id is None

def test_energydata_timestamp_defaults_to_now(db):
    """Test Case 3: EnergyData timestamp defaults to now"""
    before = datetime.datetime.utcnow()
    energy = EnergyData(generated_energy=77.7)
    db.add(energy)
    db.commit()
    db.refresh(energy)
    after = datetime.datetime.utcnow()
    assert energy.timestamp >= before
    assert energy.timestamp <= after

def test_create_energydata_with_negative_generated_energy(db, user):
    """Test Case 4: Create EnergyData with negative generated_energy"""
    energy = EnergyData(generated_energy=-42.0, user_id=user.id)
    db.add(energy)
    db.commit()
    db.refresh(energy)
    assert energy.generated_energy == -42.0

def test_create_energydata_with_null_generated_energy(db, user):
    """Test Case 5: Create EnergyData with null generated_energy"""
    energy = EnergyData(user_id=user.id)
    db.add(energy)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_create_energydata_with_invalid_user_id(db):
    """Test Case 6: Create EnergyData with invalid user_id"""
    energy = EnergyData(generated_energy=10.0, user_id=99999)
    db.add(energy)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_retrieve_energydata_records_for_a_user(db, user):
    """Test Case 7: Retrieve EnergyData records for a user"""
    e1 = EnergyData(generated_energy=1.1, user_id=user.id)
    e2 = EnergyData(generated_energy=2.2, user_id=user.id)
    db.add_all([e1, e2])
    db.commit()
    db.refresh(user)
    # Access via relationship
    user_energy = db.query(User).filter_by(id=user.id).first().energy_data
    assert len(user_energy) == 2
    assert set([ed.generated_energy for ed in user_energy]) == {1.1, 2.2}

def test_energydata_owner_relationship_returns_user(db, user):
    """Test Case 8: EnergyData owner relationship returns User"""
    energy = EnergyData(generated_energy=5.5, user_id=user.id)
    db.add(energy)
    db.commit()
    db.refresh(energy)
    assert energy.owner.id == user.id
    assert energy.owner.email == user.email

def test_energydata_id_auto_increments(db):
    """Test Case 9: EnergyData id auto-increments"""
    e1 = EnergyData(generated_energy=10.0)
    e2 = EnergyData(generated_energy=20.0)
    db.add_all([e1, e2])
    db.commit()
    db.refresh(e1)
    db.refresh(e2)
    assert e2.id == e1.id + 1

def test_create_energydata_with_large_generated_energy_value(db, user):
    """Test Case 10: Create EnergyData with large generated_energy value"""
    large_value = 1e20
    energy = EnergyData(generated_energy=large_value, user_id=user.id)
    db.add(energy)
    db.commit()
    db.refresh(energy)
    assert energy.generated_energy == large_value

def test_create_energydata_with_zero_generated_energy(db, user):
    """Test Case 11: Create EnergyData with zero generated_energy"""
    energy = EnergyData(generated_energy=0.0, user_id=user.id)
    db.add(energy)
    db.commit()
    db.refresh(energy)
    assert energy.generated_energy == 0.0

def test_create_energydata_with_future_timestamp(db, user):
    """Test Case 12: Create EnergyData with future timestamp"""
    future = datetime.datetime.utcnow() + datetime.timedelta(days=365)
    energy = EnergyData(timestamp=future, generated_energy=12.3, user_id=user.id)
    db.add(energy)
    db.commit()
    db.refresh(energy)
    assert energy.timestamp == future

def test_create_energydata_with_past_timestamp(db, user):
    """Test Case 13: Create EnergyData with past timestamp"""
    past = datetime.datetime.utcnow() - datetime.timedelta(days=365)
    energy = EnergyData(timestamp=past, generated_energy=12.3, user_id=user.id)
    db.add(energy)
    db.commit()
    db.refresh(energy)
    assert energy.timestamp == past

def test_create_energydata_with_string_as_generated_energy(db, user):
    """Test Case 14: Create EnergyData with string as generated_energy"""
    energy = EnergyData(generated_energy="not_a_float", user_id=user.id)
    db.add(energy)
    with pytest.raises((IntegrityError, ValueError, TypeError)):
        db.commit()
    db.rollback()