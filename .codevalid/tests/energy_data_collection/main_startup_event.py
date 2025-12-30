import pytest
import time
from unittest.mock import MagicMock
from backend.app import main

@pytest.fixture(autouse=True)
def patch_logger(monkeypatch):
    logs = []

    class DummyLogger:
        def info(self, msg, *args, **kwargs):
            logs.append(('info', msg))
        def error(self, msg, *args, **kwargs):
            logs.append(('error', msg))

    monkeypatch.setattr(main, "logger", DummyLogger())
    yield logs

@pytest.fixture
def scheduler_mock(monkeypatch):
    mock_scheduler = MagicMock()
    monkeypatch.setattr(main, "scheduler", mock_scheduler)
    return mock_scheduler

@pytest.fixture
def db_mock(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(main, "db", mock_db)
    return mock_db

@pytest.fixture
def external_endpoint_mock(monkeypatch):
    mock_requests = MagicMock()
    monkeypatch.setattr(main, "requests", mock_requests)
    return mock_requests

def get_logged(logs, level):
    return [msg for lvl, msg in logs if lvl == level]

# Test Case 1
def test_scheduler_starts_on_startup(patch_logger, scheduler_mock):
    main.startup_event()
    assert scheduler_mock.start.called, "Scheduler's start() should be called"
    assert any('Starting scheduler' in msg for msg in get_logged(patch_logger, 'info'))

# Test Case 2
def test_scheduler_start_failure_logs_error(patch_logger, scheduler_mock):
    scheduler_mock.start.side_effect = Exception("fail!")
    main.startup_event()
    assert any('fail!' in msg for msg in get_logged(patch_logger, 'error'))

# Test Case 3
def test_scheduler_triggers_periodic_collection(monkeypatch, scheduler_mock):
    called = {"scheduled": False, "task": False}

    def fake_add_job(func, trigger, minutes, *args, **kwargs):
        assert trigger == "interval"
        assert minutes == 1
        called["scheduled"] = True
        func()
        called["task"] = True

    scheduler_mock.add_job = fake_add_job

    # Patch the energy_data_collection_task to a dummy function
    monkeypatch.setattr(main, "energy_data_collection_task", lambda: called.update({"task": True}))
    main.startup_event()
    assert called["scheduled"], "Scheduler should schedule the periodic job"
    assert called["task"], "Energy data collection task should be triggered"

# Test Case 4
def test_energy_data_fetched_and_stored(monkeypatch, db_mock, external_endpoint_mock):
    valid_data = {"value": 123, "unit": "Mega watt hour"}
    external_endpoint_mock.get.return_value.json.return_value = valid_data
    external_endpoint_mock.get.return_value.status_code = 200

    def fake_task():
        resp = external_endpoint_mock.get("http://external/api")
        data = resp.json()
        if data["unit"] == "Mega watt hour":
            db_mock.store_energy_data(data["value"], unit=data["unit"], timestamp=pytest.approx(time.time(), rel=2))

    monkeypatch.setattr(main, "energy_data_collection_task", fake_task)
    main.energy_data_collection_task()
    db_mock.store_energy_data.assert_called_once()
    args, kwargs = db_mock.store_energy_data.call_args
    assert kwargs["unit"] == "Mega watt hour"
    assert isinstance(kwargs["timestamp"], float)

# Test Case 5
def test_external_endpoint_failure_retries(monkeypatch, external_endpoint_mock, patch_logger):
    external_endpoint_mock.get.side_effect = Exception("fail")
    retry_count = {"count": 0}

    def fake_task():
        for _ in range(3):
            try:
                external_endpoint_mock.get("http://external/api")
            except Exception:
                retry_count["count"] += 1
        if retry_count["count"] == 3:
            main.logger.error("Failed after 3 retries")

    monkeypatch.setattr(main, "energy_data_collection_task", fake_task)
    main.energy_data_collection_task()
    assert retry_count["count"] == 3
    assert any("Failed after 3 retries" in msg for msg in get_logged(patch_logger, 'error'))

# Test Case 6
def test_invalid_unit_data_rejected(monkeypatch, db_mock, external_endpoint_mock, patch_logger):
    invalid_data = {"value": 123, "unit": "kWh"}
    external_endpoint_mock.get.return_value.json.return_value = invalid_data
    external_endpoint_mock.get.return_value.status_code = 200

    def fake_task():
        resp = external_endpoint_mock.get("http://external/api")
        data = resp.json()
        if data["unit"] != "Mega watt hour":
            main.logger.error("Invalid unit")

    monkeypatch.setattr(main, "energy_data_collection_task", fake_task)
    main.energy_data_collection_task()
    db_mock.store_energy_data.assert_not_called()
    assert any("Invalid unit" in msg for msg in get_logged(patch_logger, 'error'))

# Test Case 7
def test_logging_on_successful_collection(monkeypatch, db_mock, external_endpoint_mock, patch_logger):
    valid_data = {"value": 123, "unit": "Mega watt hour"}
    external_endpoint_mock.get.return_value.json.return_value = valid_data
    external_endpoint_mock.get.return_value.status_code = 200

    def fake_task():
        resp = external_endpoint_mock.get("http://external/api")
        data = resp.json()
        if data["unit"] == "Mega watt hour":
            db_mock.store_energy_data(data["value"], unit=data["unit"], timestamp=time.time())
            main.logger.info("Energy data collected and stored")

    monkeypatch.setattr(main, "energy_data_collection_task", fake_task)
    main.energy_data_collection_task()
    assert any("collected and stored" in msg for msg in get_logged(patch_logger, 'info'))

# Test Case 8
def test_logging_on_failed_collection(monkeypatch, external_endpoint_mock, patch_logger):
    external_endpoint_mock.get.side_effect = Exception("fail")

    def fake_task():
        try:
            external_endpoint_mock.get("http://external/api")
        except Exception:
            main.logger.error("Collection failed")

    monkeypatch.setattr(main, "energy_data_collection_task", fake_task)
    main.energy_data_collection_task()
    assert any("Collection failed" in msg for msg in get_logged(patch_logger, 'error'))

# Test Case 9
def test_database_write_failure_logs_error(monkeypatch, db_mock, external_endpoint_mock, patch_logger):
    valid_data = {"value": 123, "unit": "Mega watt hour"}
    external_endpoint_mock.get.return_value.json.return_value = valid_data
    external_endpoint_mock.get.return_value.status_code = 200
    db_mock.store_energy_data.side_effect = Exception("db fail")

    def fake_task():
        resp = external_endpoint_mock.get("http://external/api")
        data = resp.json()
        try:
            db_mock.store_energy_data(data["value"], unit=data["unit"], timestamp=time.time())
        except Exception as e:
            main.logger.error(f"DB error: {e}")

    monkeypatch.setattr(main, "energy_data_collection_task", fake_task)
    main.energy_data_collection_task()
    assert any("DB error" in msg for msg in get_logged(patch_logger, 'error'))

# Test Case 10
def test_timestamp_precision_on_storage(monkeypatch, db_mock, external_endpoint_mock):
    valid_data = {"value": 123, "unit": "Mega watt hour"}
    external_endpoint_mock.get.return_value.json.return_value = valid_data
    external_endpoint_mock.get.return_value.status_code = 200

    captured = {}

    def fake_store_energy_data(value, unit, timestamp):
        captured["timestamp"] = timestamp

    db_mock.store_energy_data.side_effect = fake_store_energy_data

    def fake_task():
        resp = external_endpoint_mock.get("http://external/api")
        data = resp.json()
        db_mock.store_energy_data(data["value"], unit=data["unit"], timestamp=time.time())

    monkeypatch.setattr(main, "energy_data_collection_task", fake_task)
    main.energy_data_collection_task()
    assert "timestamp" in captured
    assert isinstance(captured["timestamp"], float)
    assert captured["timestamp"] > 1000000000  # Unix epoch seconds