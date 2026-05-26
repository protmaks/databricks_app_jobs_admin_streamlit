"""Pytest configuration and shared fixtures."""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from databricks.sdk import WorkspaceClient

# Mock streamlit before any imports that use it
if "streamlit" not in sys.modules:
    streamlit_mock = MagicMock()
    streamlit_mock.session_state = {}
    streamlit_mock.cache_data = lambda *args, **kwargs: lambda func: func
    streamlit_mock.cache_resource = lambda *args, **kwargs: lambda func: func
    sys.modules["streamlit"] = streamlit_mock


@pytest.fixture
def mock_workspace_client():
    """Mock Databricks WorkspaceClient for testing."""
    mock_client = Mock(spec=WorkspaceClient)
    mock_client.workspace = MagicMock()
    mock_client.jobs = MagicMock()
    return mock_client


@pytest.fixture
def sample_settings():
    """Sample settings configuration for testing."""
    return {
        "version": 1,
        "timezone": "UTC",
        "teams": [
            {
                "id": "team1",
                "name": "Data Team",
                "conditions": [
                    {
                        "field": "job_name",
                        "operator": "starts_with",
                        "value": "data_"
                    }
                ],
                "logic": "OR"
            },
            {
                "id": "team2",
                "name": "ML Team",
                "conditions": [
                    {
                        "field": "creator",
                        "operator": "contains",
                        "value": "ml-team"
                    }
                ],
                "logic": "OR"
            }
        ]
    }


@pytest.fixture
def sample_user_prefs():
    """Sample user preferences for testing."""
    return {
        "default_teams": ["team1"],
        "last_timezone": "US/Pacific"
    }


@pytest.fixture
def temp_test_dir(tmp_path):
    """Temporary directory for file operations testing."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for all tests."""
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "test_token")
