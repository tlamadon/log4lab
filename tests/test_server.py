"""Tests for Log4Lab server endpoints."""
import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from log4lab import server


@pytest.fixture
def temp_log_file():
    """Create a temporary log file with test data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        # Write test log entries
        logs = [
            {
                "time": "2025-10-24T10:00:00Z",
                "level": "INFO",
                "section": "test",
                "message": "First log entry",
                "run_name": "test_run",
                "run_id": "run_001",
                "group": "test_group"
            },
            {
                "time": "2025-10-24T10:05:00Z",
                "level": "ERROR",
                "section": "test",
                "message": "Error log entry",
                "run_name": "test_run",
                "run_id": "run_001"
            },
            {
                "time": "2025-10-24T11:00:00Z",
                "level": "INFO",
                "section": "another",
                "message": "Different run",
                "run_name": "test_run",
                "run_id": "run_002"
            },
            {
                "time": "2025-10-24T12:00:00Z",
                "level": "DEBUG",
                "section": "debug",
                "message": "Debug message",
                "run_name": "another_run",
                "run_id": "run_003"
            }
        ]
        for log in logs:
            f.write(json.dumps(log) + '\n')
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink()


@pytest.fixture
def client(temp_log_file):
    """Create a test client with a temporary log file."""
    server.set_log_path(temp_log_file)
    return TestClient(server.app)


def test_index_page(client):
    """Test that the index page loads successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Log4Lab" in response.text
    assert "Live" in response.text


def test_runs_page(client):
    """Test that the runs index page loads successfully."""
    response = client.get("/runs")
    assert response.status_code == 200
    assert "Log4Lab" in response.text
    assert "Runs Index" in response.text


def test_api_runs_endpoint(client, temp_log_file):
    """Test the /api/runs endpoint returns correct data structure."""
    response = client.get("/api/runs")
    assert response.status_code == 200

    data = response.json()
    assert "runs" in data

    # Check that we have the expected run names
    assert "test_run" in data["runs"]
    assert "another_run" in data["runs"]

    # Check test_run structure
    test_run = data["runs"]["test_run"]
    assert "total" in test_run
    assert "run_ids" in test_run
    assert test_run["total"] == 3  # Three entries for test_run

    # Check run_ids structure
    assert len(test_run["run_ids"]) == 2  # run_001 and run_002

    run_id_001 = next(r for r in test_run["run_ids"] if r["run_id"] == "run_001")
    assert run_id_001["count"] == 2
    assert run_id_001["earliest"] == "2025-10-24T10:00:00Z"
    assert run_id_001["latest"] == "2025-10-24T10:05:00Z"

    run_id_002 = next(r for r in test_run["run_ids"] if r["run_id"] == "run_002")
    assert run_id_002["count"] == 1
    assert run_id_002["earliest"] == "2025-10-24T11:00:00Z"


def test_api_runs_empty_file():
    """Test /api/runs with an empty log file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = Path(f.name)

    try:
        server.set_log_path(temp_path)
        client = TestClient(server.app)

        response = client.get("/api/runs")
        assert response.status_code == 200

        data = response.json()
        assert data["runs"] == {}
    finally:
        temp_path.unlink()


def test_api_runs_no_run_fields():
    """Test /api/runs with logs that don't have run_name/run_id fields."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        logs = [
            {"time": "2025-10-24T10:00:00Z", "level": "INFO", "message": "No run info"},
            {"time": "2025-10-24T10:05:00Z", "level": "ERROR", "message": "Another entry"}
        ]
        for log in logs:
            f.write(json.dumps(log) + '\n')
        temp_path = Path(f.name)

    try:
        server.set_log_path(temp_path)
        client = TestClient(server.app)

        response = client.get("/api/runs")
        assert response.status_code == 200

        data = response.json()
        assert data["runs"] == {}
    finally:
        temp_path.unlink()


def test_cache_file_serving(client, temp_log_file):
    """Test serving cache files from the log directory."""
    # Create a test file in the same directory as the log file
    log_dir = temp_log_file.parent
    test_file = log_dir / "test_artifact.txt"
    test_file.write_text("Test artifact content")

    try:
        response = client.get("/cache/test_artifact.txt")
        assert response.status_code == 200
        assert response.text == "Test artifact content"
    finally:
        test_file.unlink()


def test_cache_file_not_found(client):
    """Test that non-existent cache files return 404."""
    response = client.get("/cache/nonexistent.txt")
    assert response.status_code == 404


def test_cache_file_path_traversal_protection(client):
    """Test that path traversal attacks are blocked."""
    response = client.get("/cache/../../../etc/passwd")
    # Should return an error code (403, 400, or 404 if path doesn't resolve)
    assert response.status_code in [403, 400, 404]
    # Most importantly, should NOT return 200
    assert response.status_code != 200


def test_get_set_log_path(temp_log_file):
    """Test the get_log_path and set_log_path functions."""
    server.set_log_path(temp_log_file)
    assert server.get_log_path() == temp_log_file


def test_invalid_json_lines(client):
    """Test that invalid JSON lines are skipped gracefully."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"valid": "json"}\n')
        f.write('invalid json line\n')
        f.write('{"another": "valid", "run_name": "test", "run_id": "1"}\n')
        temp_path = Path(f.name)

    try:
        server.set_log_path(temp_path)
        client = TestClient(server.app)

        response = client.get("/api/runs")
        assert response.status_code == 200

        data = response.json()
        # Should only count the valid entries with run info
        assert len(data["runs"]) == 1
        assert "test" in data["runs"]
    finally:
        temp_path.unlink()
