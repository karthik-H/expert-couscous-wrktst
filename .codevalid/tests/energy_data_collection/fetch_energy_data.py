import pytest
from unittest import mock
from unittest.mock import patch, MagicMock
import datetime

import backend.app.services.scheduler as scheduler

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

def test_successful_fetch_on_first_attempt(
    patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime
):
    patch_random.return_value = 42.5
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    assert patch_random.call_count == 1
    patch_logger.info.assert_any_call("Fetching energy data...")
    patch_logger.info.assert_any_call("Data saved")
    patch_energydata.assert_called_once()
    patch_db_session.add.assert_called_once_with(instance)
    patch_db_session.commit.assert_called_once()

def test_successful_fetch_on_second_attempt(
    patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime
):
    patch_random.side_effect = [Exception("fail"), 77.0]
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    assert patch_random.call_count == 2
    patch_logger.error.assert_any_call(mock.ANY)
    patch_logger.info.assert_any_call("Data saved")
    patch_energydata.assert_called_once()
    patch_db_session.add.assert_called_once_with(instance)
    patch_db_session.commit.assert_called_once()

def test_successful_fetch_on_third_attempt(
    patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime
):
    patch_random.side_effect = [Exception("fail1"), Exception("fail2"), 88.0]
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    assert patch_random.call_count == 3
    patch_logger.error.assert_any_call(mock.ANY)
    patch_logger.info.assert_any_call("Data saved")
    patch_energydata.assert_called_once()
    patch_db_session.add.assert_called_once_with(instance)
    patch_db_session.commit.assert_called_once()

def test_all_attempts_fail(
    patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime
):
    patch_random.side_effect = [Exception("fail1"), Exception("fail2"), Exception("fail3")]
    scheduler.fetch_energy_data()
    assert patch_random.call_count == 3
    patch_logger.error.assert_any_call(mock.ANY)
    patch_logger.error.assert_any_call("Max retries reached. Data fetch failed.")
    patch_db_session.add.assert_not_called()
    patch_db_session.commit.assert_not_called()
    patch_energydata.assert_not_called()

def test_db_commit_failure(
    patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime
):
    patch_random.return_value = 12.0
    instance = MagicMock()
    patch_energydata.return_value = instance
    patch_db_session.commit.side_effect = [Exception("db fail"), Exception("db fail"), Exception("db fail")]
    scheduler.fetch_energy_data()
    assert patch_db_session.commit.call_count == 3
    assert patch_db_session.add.call_count == 3
    patch_logger.error.assert_any_call(mock.ANY)
    patch_logger.error.assert_any_call("Max retries reached. Data fetch failed.")

def test_invalid_unit_rejected(
    patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime
):
    patch_random.return_value = 42.0
    patch_energydata.side_effect = ValueError("Invalid unit")
    scheduler.fetch_energy_data()
    assert patch_energydata.call_count == 3
    patch_logger.error.assert_any_call(mock.ANY)
    patch_logger.error.assert_any_call("Max retries reached. Data fetch failed.")
    patch_db_session.add.assert_not_called()
    patch_db_session.commit.assert_not_called()

def test_logging_on_each_attempt(
    patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime
):
    patch_random.side_effect = [Exception("fail"), 33.0]
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    patch_logger.info.assert_any_call("Fetching energy data...")
    patch_logger.error.assert_any_call(mock.ANY)
    patch_logger.info.assert_any_call("Data saved")

def test_zero_value_energy_data(
    patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime
):
    patch_random.return_value = 0.0
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    patch_logger.info.assert_any_call("Data saved")
    patch_db_session.add.assert_called_once_with(instance)
    patch_db_session.commit.assert_called_once()

def test_large_value_energy_data(
    patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime
):
    patch_random.return_value = 1e9
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    patch_logger.info.assert_any_call("Data saved")
    patch_db_session.add.assert_called_once_with(instance)
    patch_db_session.commit.assert_called_once()

def test_timestamp_accuracy(
    patch_db_session, patch_logger, patch_energydata, patch_random, patch_datetime
):
    patch_random.return_value = 123.45
    instance = MagicMock()
    patch_energydata.return_value = instance
    scheduler.fetch_energy_data()
    args, kwargs = patch_energydata.call_args
    ts = kwargs.get("timestamp")
    assert ts is not None
    assert abs((ts - patch_datetime).total_seconds()) < 1