import pytest
from unittest import mock
from unittest.mock import patch, MagicMock, call
import datetime

import backend.app.services.scheduler as scheduler
from backend.app.models import EnergyData
from backend.app.database import SessionLocal

@pytest.fixture(autouse=True)
def patch_db_session(monkeypatch):
    """Patch SessionLocal to use a mock session for all tests."""
    mock_session = MagicMock()
    monkeypatch.setattr(scheduler.database, "SessionLocal", lambda: mock_session)
    yield mock_session

@pytest.fixture(autouse=True)
def patch_logger(monkeypatch):
    """Patch logger to a mock for all tests."""
    mock_logger = MagicMock()
    monkeypatch.setattr(scheduler, "logger", mock_logger)
    yield mock_logger

@pytest.fixture(autouse=True)
def patch_energydata(monkeypatch):
    """Patch EnergyData to a MagicMock for all tests."""
    mock_energydata = MagicMock()
    monkeypatch.setattr(scheduler.models, "EnergyData", mock_energydata)
    yield mock_energydata

@pytest.fixture(autouse=True)
def patch_random(monkeypatch):
    """Patch random.uniform to a MagicMock for all tests."""
    with patch("backend.app.services.scheduler.random.uniform") as mock_random:
        yield mock_random

@pytest.fixture(autouse=True)
def patch_datetime(monkeypatch):
    """Patch datetime.datetime.utcnow to a controllable value."""
    fixed_now = datetime.datetime(2025, 1, 1, 12, 0, 0)
    class FixedDatetime(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return fixed_now
    monkeypatch.setattr(scheduler.datetime, "datetime", FixedDatetime)
    yield fixed_now

def _run_and_assert_attempts(monkeypatch, random_side_effects, commit_side_effects, expected_attempts, expect_success, expect_data_saved, expect_max_retries, unit="kWh", value=42.0):
    """Helper to run fetch_energy_data with controlled side effects and assert behavior."""
    # Patch random.uniform to simulate fetch
    with patch("backend.app.services.scheduler.random.uniform", side_effect=random_side_effects) as mock_random:
        # Patch EnergyData to check instantiation
        with patch.object(scheduler.models, "EnergyData") as mock_energydata:
            # Patch DB session
            mock_session = MagicMock()
            mock_commit = mock_session.commit
            mock_commit.side_effect = commit_side_effects
            monkeypatch.setattr(scheduler.database, "SessionLocal", lambda: mock_session)
            # Patch logger
            mock_logger = MagicMock()
            monkeypatch.setattr(scheduler, "logger", mock_logger)
            # Patch datetime
            fixed_now = datetime.datetime(2025, 1, 1, 12, 0, 0)
            class FixedDatetime(datetime.datetime):
                @classmethod
                def utcnow(cls):
                    return fixed_now
            monkeypatch.setattr(scheduler.datetime, "datetime", FixedDatetime)
            # Patch EnergyData to simulate unit
            def energydata_side_effect(*args, **kwargs):
                # Simulate unit check
                if unit != "kWh":
                    raise ValueError("Invalid unit")
                return MagicMock()
            mock_energydata.side_effect = energydata_side_effect if unit != "kWh" else None
            # Run
            scheduler.fetch_energy_data()
            # Assertions
            assert mock_random.call_count == expected_attempts
            if expect_success:
                assert mock_energydata.call_count == 1
                assert mock_commit.call_count == 1
                mock_logger.info.assert_any_call("Data saved: {:.2f} kWh".format(value))
            else:
                assert mock_commit.call_count == expected_attempts if commit_side_effects else 0
            if expect_max_retries:
                mock_logger.error.assert_any_call("Max retries reached. Data fetch failed.")

def test_successful_fetch_on_first_attempt(monkeypatch, patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime):
    patch_random.return_value = 50.0
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    # Only one attempt
    assert patch_random.call_count == 1
    patch_logger.info.assert_any_call("Fetching energy data...")
    patch_logger.info.assert_any_call("Data saved: 50.00 kWh")
    patch_energydata.assert_called_once()
    patch_db_session.add.assert_called_once_with(instance)
    patch_db_session.commit.assert_called_once()

def test_successful_fetch_on_second_attempt(monkeypatch, patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime):
    patch_random.side_effect = [Exception("fail"), 77.0]
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    assert patch_random.call_count == 2
    patch_logger.error.assert_any_call(mock.ANY)
    patch_logger.info.assert_any_call("Data saved: 77.00 kWh")
    patch_energydata.assert_called_once()
    patch_db_session.add.assert_called_once_with(instance)
    patch_db_session.commit.assert_called_once()

def test_successful_fetch_on_third_attempt(monkeypatch, patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime):
    patch_random.side_effect = [Exception("fail1"), Exception("fail2"), 88.0]
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    assert patch_random.call_count == 3
    patch_logger.error.assert_any_call(mock.ANY)
    patch_logger.info.assert_any_call("Data saved: 88.00 kWh")
    patch_energydata.assert_called_once()
    patch_db_session.add.assert_called_once_with(instance)
    patch_db_session.commit.assert_called_once()

def test_all_attempts_fail(monkeypatch, patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime):
    patch_random.side_effect = [Exception("fail1"), Exception("fail2"), Exception("fail3")]
    scheduler.fetch_energy_data()
    assert patch_random.call_count == 3
    assert patch_db_session.add.call_count == 0
    assert patch_db_session.commit.call_count == 0
    patch_logger.error.assert_any_call("Max retries reached. Data fetch failed.")

def test_db_commit_failure(monkeypatch, patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime):
    patch_random.return_value = 12.0
    instance = MagicMock()
    patch_energydata.return_value = instance
    patch_db_session.commit.side_effect = [Exception("db fail"), Exception("db fail"), Exception("db fail")]
    scheduler.fetch_energy_data()
    assert patch_db_session.commit.call_count == 3
    assert patch_db_session.add.call_count == 3
    patch_logger.error.assert_any_call("Max retries reached. Data fetch failed.")

def test_invalid_unit_rejected(monkeypatch, patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime):
    # Simulate EnergyData raising ValueError for invalid unit
    patch_random.return_value = 42.0
    patch_energydata.side_effect = ValueError("Invalid unit")
    scheduler.fetch_energy_data()
    assert patch_energydata.call_count == 3
    assert patch_db_session.add.call_count == 0
    assert patch_db_session.commit.call_count == 0
    patch_logger.error.assert_any_call(mock.ANY)
    patch_logger.error.assert_any_call("Max retries reached. Data fetch failed.")

def test_logging_on_each_attempt(monkeypatch, patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime):
    patch_random.side_effect = [Exception("fail"), 33.0]
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    patch_logger.info.assert_any_call("Fetching energy data...")
    patch_logger.error.assert_any_call(mock.ANY)
    patch_logger.info.assert_any_call("Data saved: 33.00 kWh")

def test_zero_value_energy_data(monkeypatch, patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime):
    patch_random.return_value = 0.0
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    patch_logger.info.assert_any_call("Data saved: 0.00 kWh")
    patch_db_session.add.assert_called_once_with(instance)
    patch_db_session.commit.assert_called_once()

def test_large_value_energy_data(monkeypatch, patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime):
    patch_random.return_value = 1e9
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    patch_logger.info.assert_any_call("Data saved: 1000000000.00 kWh")
    patch_db_session.add.assert_called_once_with(instance)
    patch_db_session.commit.assert_called_once()

def test_timestamp_accuracy(monkeypatch, patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime):
    patch_random.return_value = 123.45
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    args, kwargs = patch_energydata.call_args
    # The timestamp argument should be close to the fixed time
    ts = kwargs.get("timestamp")
    assert ts is not None
    assert abs((ts - patch_datetime).total_seconds()) < 1