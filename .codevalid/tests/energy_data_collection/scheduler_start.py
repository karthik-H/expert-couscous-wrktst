import pytest
from unittest.mock import patch, MagicMock, call

import backend.app.services.scheduler as scheduler_mod

@pytest.fixture(autouse=True)
def reset_scheduler():
    # Ensure scheduler is shutdown and jobs are cleared before/after each test
    try:
        scheduler_mod.scheduler.shutdown(wait=False)
    except Exception:
        pass
    scheduler_mod.scheduler = scheduler_mod.BackgroundScheduler()
    yield
    try:
        scheduler_mod.scheduler.shutdown(wait=False)
    except Exception:
        pass
    scheduler_mod.scheduler = scheduler_mod.BackgroundScheduler()

def test_scheduler_runs_every_minute():
    with patch.object(scheduler_mod.scheduler, "add_job") as mock_add_job:
        scheduler_mod.start()
        mock_add_job.assert_called_once()
        args, kwargs = mock_add_job.call_args
        assert args[0] == scheduler_mod.fetch_energy_data
        assert kwargs["trigger"] == "interval"
        assert kwargs["minutes"] == 1

def test_scheduler_starts():
    with patch.object(scheduler_mod.scheduler, "start") as mock_start:
        scheduler_mod.start()
        mock_start.assert_called_once()

def test_fetch_energy_data_retries_on_failure():
    # Simulate fetch_energy_data raising exception, ensure 3 retries
    with patch.object(scheduler_mod, "fetch_energy_data") as mock_fetch:
        mock_fetch.side_effect = Exception("fail")
        with patch.object(scheduler_mod.scheduler, "add_job") as mock_add_job:
            scheduler_mod.start()
            # Simulate job function (should retry 3 times)
            job_func = mock_add_job.call_args[0][0]
            with patch("backend.app.services.scheduler.logger") as mock_logger:
                job_func()
                assert mock_fetch.call_count == 3
                assert mock_logger.error.call_count >= 1

def test_logs_error_on_fetch_failure():
    # Simulate fetch_energy_data raising exception, ensure error is logged
    with patch.object(scheduler_mod, "fetch_energy_data") as mock_fetch:
        mock_fetch.side_effect = Exception("fail")
        with patch.object(scheduler_mod.scheduler, "add_job") as mock_add_job:
            scheduler_mod.start()
            job_func = mock_add_job.call_args[0][0]
            with patch("backend.app.services.scheduler.logger") as mock_logger:
                job_func()
                assert mock_logger.error.called

def test_invalid_unit_rejected():
    # Simulate fetch_energy_data returning data with invalid unit
    with patch.object(scheduler_mod, "fetch_energy_data") as mock_fetch:
        mock_fetch.return_value = {"value": 10, "unit": "kWh", "timestamp": "2025-01-01T00:00:00Z"}
        with patch.object(scheduler_mod.scheduler, "add_job") as mock_add_job:
            scheduler_mod.start()
            job_func = mock_add_job.call_args[0][0]
            with patch("backend.app.services.scheduler.logger") as mock_logger, \
                 patch("backend.app.services.scheduler.database") as mock_db:
                job_func()
                # Should not store in DB and should log error
                assert not mock_db.SessionLocal.return_value.add.called
                assert mock_logger.error.called

def test_valid_data_stored():
    # Simulate fetch_energy_data returning valid data
    valid_data = {"value": 100, "unit": "Mega watt hour", "timestamp": "2025-01-01T00:00:00Z"}
    with patch.object(scheduler_mod, "fetch_energy_data") as mock_fetch:
        mock_fetch.return_value = valid_data
        with patch.object(scheduler_mod.scheduler, "add_job") as mock_add_job:
            scheduler_mod.start()
            job_func = mock_add_job.call_args[0][0]
            with patch("backend.app.services.scheduler.database") as mock_db, \
                 patch("backend.app.services.scheduler.models") as mock_models:
                session = MagicMock()
                mock_db.SessionLocal.return_value = session
                mock_models.EnergyData.return_value = MagicMock()
                job_func()
                session.add.assert_called()
                session.commit.assert_called()

def test_scheduler_already_running():
    # Simulate scheduler already running
    with patch.object(scheduler_mod.scheduler, "running", True):
        with patch.object(scheduler_mod.scheduler, "add_job") as mock_add_job, \
             patch.object(scheduler_mod.scheduler, "start") as mock_start:
            scheduler_mod.start()
            # Should not duplicate jobs or error
            mock_add_job.assert_not_called()
            mock_start.assert_not_called()

def test_external_endpoint_unreachable():
    # Simulate fetch_energy_data raising network error
    with patch.object(scheduler_mod, "fetch_energy_data") as mock_fetch:
        mock_fetch.side_effect = Exception("Network error")
        with patch.object(scheduler_mod.scheduler, "add_job") as mock_add_job:
            scheduler_mod.start()
            job_func = mock_add_job.call_args[0][0]
            with patch("backend.app.services.scheduler.logger") as mock_logger:
                job_func()
                assert mock_fetch.call_count == 3
                assert mock_logger.error.called

def test_scheduler_shutdown_and_restart():
    # Start, shutdown, and restart scheduler
    scheduler_mod.start()
    scheduler_mod.shutdown()
    with patch.object(scheduler_mod.scheduler, "add_job") as mock_add_job, \
         patch.object(scheduler_mod.scheduler, "start") as mock_start:
        scheduler_mod.start()
        mock_add_job.assert_called_once()
        mock_start.assert_called_once()

def test_database_write_failure():
    # Simulate DB write failure during data storage
    valid_data = {"value": 100, "unit": "Mega watt hour", "timestamp": "2025-01-01T00:00:00Z"}
    with patch.object(scheduler_mod, "fetch_energy_data") as mock_fetch:
        mock_fetch.return_value = valid_data
        with patch.object(scheduler_mod.scheduler, "add_job") as mock_add_job:
            scheduler_mod.start()
            job_func = mock_add_job.call_args[0][0]
            with patch("backend.app.services.scheduler.database") as mock_db, \
                 patch("backend.app.services.scheduler.models") as mock_models, \
                 patch("backend.app.services.scheduler.logger") as mock_logger:
                session = MagicMock()
                session.add.side_effect = Exception("DB write error")
                mock_db.SessionLocal.return_value = session
                mock_models.EnergyData.return_value = MagicMock()
                job_func()
                assert mock_logger.error.called