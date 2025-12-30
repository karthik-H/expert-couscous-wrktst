import pytest
from datetime import datetime
from pydantic import ValidationError

# Import the EnergyData schema from the backend implementation
from backend.app.schemas import EnergyData

# Test Case 1: test_valid_energydata_full_input
def test_valid_energydata_full_input():
    data = EnergyData(
        id=1,
        timestamp=datetime(2023, 1, 1, 12, 0),
        generated_energy=123.45,
        user_id=10
    )
    assert data.id == 1
    assert data.timestamp == datetime(2023, 1, 1, 12, 0)
    assert data.generated_energy == 123.45
    assert data.user_id == 10

# Test Case 2: test_valid_energydata_without_userid
def test_valid_energydata_without_userid():
    data = EnergyData(
        id=2,
        timestamp=datetime(2023, 1, 2, 13, 0),
        generated_energy=67.89
    )
    assert data.id == 2
    assert data.timestamp == datetime(2023, 1, 2, 13, 0)
    assert data.generated_energy == 67.89
    assert data.user_id is None

# Test Case 3: test_energydata_id_as_string
def test_energydata_id_as_string():
    with pytest.raises(ValidationError) as exc_info:
        EnergyData(
            id='abc',
            timestamp=datetime(2023, 1, 1, 12, 0),
            generated_energy=123.45,
            user_id=10
        )
    assert 'id' in str(exc_info.value)

# Test Case 4: test_energydata_missing_id
def test_energydata_missing_id():
    with pytest.raises(ValidationError) as exc_info:
        EnergyData(
            timestamp=datetime(2023, 1, 1, 12, 0),
            generated_energy=123.45,
            user_id=10
        )
    assert 'id' in str(exc_info.value)

# Test Case 5: test_energydata_generated_energy_as_string
def test_energydata_generated_energy_as_string():
    with pytest.raises(ValidationError) as exc_info:
        EnergyData(
            id=3,
            timestamp=datetime(2023, 1, 3, 14, 0),
            generated_energy='high',
            user_id=11
        )
    assert 'generated_energy' in str(exc_info.value)

# Test Case 6: test_energydata_timestamp_as_string
def test_energydata_timestamp_as_string():
    data = EnergyData(
        id=4,
        timestamp='2023-01-04T15:00:00',
        generated_energy=200.0,
        user_id=12
    )
    assert data.id == 4
    assert data.timestamp == datetime(2023, 1, 4, 15, 0)
    assert data.generated_energy == 200.0
    assert data.user_id == 12

# Test Case 7: test_energydata_timestamp_invalid_format
def test_energydata_timestamp_invalid_format():
    with pytest.raises(ValidationError) as exc_info:
        EnergyData(
            id=5,
            timestamp='not-a-date',
            generated_energy=50.0,
            user_id=13
        )
    assert 'timestamp' in str(exc_info.value)

# Test Case 8: test_energydata_userid_none
def test_energydata_userid_none():
    data = EnergyData(
        id=6,
        timestamp=datetime(2023, 1, 5, 16, 0),
        generated_energy=0.0,
        user_id=None
    )
    assert data.id == 6
    assert data.timestamp == datetime(2023, 1, 5, 16, 0)
    assert data.generated_energy == 0.0
    assert data.user_id is None

# Test Case 9: test_energydata_generated_energy_zero
def test_energydata_generated_energy_zero():
    data = EnergyData(
        id=7,
        timestamp=datetime(2023, 1, 6, 17, 0),
        generated_energy=0.0,
        user_id=14
    )
    assert data.id == 7
    assert data.timestamp == datetime(2023, 1, 6, 17, 0)
    assert data.generated_energy == 0.0
    assert data.user_id == 14

# Test Case 10: test_energydata_generated_energy_negative
def test_energydata_generated_energy_negative():
    data = EnergyData(
        id=8,
        timestamp=datetime(2023, 1, 7, 18, 0),
        generated_energy=-10.5,
        user_id=15
    )
    assert data.id == 8
    assert data.timestamp == datetime(2023, 1, 7, 18, 0)
    assert data.generated_energy == -10.5
    assert data.user_id == 15

# Test Case 11: test_energydata_extra_field
def test_energydata_extra_field():
    with pytest.raises(ValidationError) as exc_info:
        EnergyData(
            id=9,
            timestamp=datetime(2023, 1, 8, 19, 0),
            generated_energy=99.9,
            user_id=16,
            extra_field='extra'
        )
    assert 'extra_field' in str(exc_info.value)

# Test Case 12: test_energydata_id_boundary
def test_energydata_id_boundary():
    data = EnergyData(
        id=0,
        timestamp=datetime(2023, 1, 9, 20, 0),
        generated_energy=1.0,
        user_id=17
    )
    assert data.id == 0
    assert data.timestamp == datetime(2023, 1, 9, 20, 0)
    assert data.generated_energy == 1.0
    assert data.user_id == 17