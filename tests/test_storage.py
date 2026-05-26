"""Tests for pages/settings/storage.py module."""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from databricks.sdk.service.workspace import ExportFormat, ImportFormat
from pages.settings.storage import (
    load_settings,
    save_settings,
    DEFAULT_SETTINGS,
    _migrate,
    _ws_read,
    _ws_write,
)


class TestMigrate:
    """Tests for _migrate function."""

    def test_migrate_adds_missing_fields(self):
        """Test that migrate adds missing default_teams field."""
        data = {"version": 1, "timezone": "UTC", "teams": []}
        result = _migrate(data)
        assert "default_teams" in result
        assert result["default_teams"] == []

    def test_migrate_preserves_existing_fields(self):
        """Test that migrate preserves existing fields."""
        data = {
            "version": 1,
            "timezone": "US/Pacific",
            "teams": [{"name": "Test"}],
            "default_teams": ["team1"]
        }
        result = _migrate(data)
        assert result["timezone"] == "US/Pacific"
        assert result["teams"] == [{"name": "Test"}]
        assert result["default_teams"] == ["team1"]


class TestWorkspaceFileHelpers:
    """Tests for workspace file helper functions."""

    def test_ws_read(self, mock_workspace_client):
        """Test reading from workspace files."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = "eyJ0ZXN0IjogImRhdGEifQ=="  # base64 of {"test": "data"}
        mock_workspace_client.workspace.export.return_value = mock_response

        result = _ws_read(mock_workspace_client, "/test/path.json")
        
        assert result == b'{"test": "data"}'
        mock_workspace_client.workspace.export.assert_called_once_with(
            path="/test/path.json",
            format=ExportFormat.SOURCE
        )

    def test_ws_write(self, mock_workspace_client):
        """Test writing to workspace files."""
        test_data = b'{"test": "data"}'
        
        _ws_write(mock_workspace_client, "/test/path.json", test_data)
        
        mock_workspace_client.workspace.mkdirs.assert_called_once_with(path="/test")
        mock_workspace_client.workspace.import_.assert_called_once()
        call_args = mock_workspace_client.workspace.import_.call_args
        assert call_args.kwargs["path"] == "/test/path.json"
        assert call_args.kwargs["format"] == ImportFormat.AUTO
        assert call_args.kwargs["overwrite"] is True

    def test_ws_write_creates_parent_dir(self, mock_workspace_client):
        """Test that ws_write creates parent directory."""
        test_data = b'{"test": "data"}'
        
        _ws_write(mock_workspace_client, "/a/b/c/file.json", test_data)
        
        mock_workspace_client.workspace.mkdirs.assert_called_once_with(path="/a/b/c")

    def test_ws_write_ignores_mkdir_errors(self, mock_workspace_client):
        """Test that ws_write continues even if mkdir fails."""
        mock_workspace_client.workspace.mkdirs.side_effect = Exception("Permission denied")
        test_data = b'{"test": "data"}'
        
        # Should not raise exception
        _ws_write(mock_workspace_client, "/test/path.json", test_data)
        
        mock_workspace_client.workspace.import_.assert_called_once()


class TestLoadSettings:
    """Tests for load_settings function."""

    def test_load_settings_from_workspace(self, mock_workspace_client):
        """Test loading settings from workspace successfully."""
        settings_data = {
            "version": 1,
            "timezone": "US/Pacific",
            "teams": [{"name": "Test Team"}]
        }
        mock_response = Mock()
        import base64
        mock_response.content = base64.b64encode(
            json.dumps(settings_data).encode("utf-8")
        ).decode("ascii")
        mock_workspace_client.workspace.export.return_value = mock_response

        result = load_settings(mock_workspace_client)
        
        assert result["version"] == 1
        assert result["timezone"] == "US/Pacific"
        assert "default_teams" in result  # added by migration

    def test_load_settings_wrong_version(self, mock_workspace_client):
        """Test loading settings with wrong version returns defaults."""
        settings_data = {"version": 999, "timezone": "UTC"}
        mock_response = Mock()
        import base64
        mock_response.content = base64.b64encode(
            json.dumps(settings_data).encode("utf-8")
        ).decode("ascii")
        mock_workspace_client.workspace.export.return_value = mock_response

        result = load_settings(mock_workspace_client)
        
        assert result == DEFAULT_SETTINGS

    @patch("pages.settings.storage._load_local")
    def test_load_settings_fallback_to_local(self, mock_load_local, mock_workspace_client):
        """Test fallback to local file when workspace read fails."""
        mock_workspace_client.workspace.export.side_effect = Exception("Network error")
        mock_load_local.return_value = {"version": 1, "timezone": "UTC", "teams": []}

        result = load_settings(mock_workspace_client)
        
        mock_load_local.assert_called_once()
        assert result["timezone"] == "UTC"


class TestSaveSettings:
    """Tests for save_settings function."""

    def test_save_settings_to_workspace(self, mock_workspace_client):
        """Test saving settings to workspace successfully."""
        settings = {
            "version": 1,
            "timezone": "US/Pacific",
            "teams": [{"name": "Test"}]
        }
        
        save_settings(mock_workspace_client, settings)
        
        mock_workspace_client.workspace.import_.assert_called_once()

    @patch("pages.settings.storage._save_local")
    def test_save_settings_fallback_to_local(self, mock_save_local, mock_workspace_client):
        """Test fallback to local file when workspace write fails."""
        mock_workspace_client.workspace.import_.side_effect = Exception("Permission denied")
        settings = {"version": 1, "timezone": "UTC", "teams": []}
        
        save_settings(mock_workspace_client, settings)
        
        mock_save_local.assert_called_once_with(settings)

    @patch("pages.settings.storage._save_local")
    def test_save_settings_raises_when_both_fail(self, mock_save_local, mock_workspace_client):
        """Test that RuntimeError is raised when both saves fail."""
        mock_workspace_client.workspace.import_.side_effect = Exception("WS error")
        mock_save_local.side_effect = Exception("Local error")
        settings = {"version": 1, "timezone": "UTC", "teams": []}
        
        with pytest.raises(RuntimeError) as exc_info:
            save_settings(mock_workspace_client, settings)
        
        assert "Failed to save settings" in str(exc_info.value)


class TestDefaultSettings:
    """Tests for DEFAULT_SETTINGS constant."""

    def test_default_settings_structure(self):
        """Test that DEFAULT_SETTINGS has expected structure."""
        assert DEFAULT_SETTINGS["version"] == 1
        assert "timezone" in DEFAULT_SETTINGS
        assert "teams" in DEFAULT_SETTINGS
        assert isinstance(DEFAULT_SETTINGS["teams"], list)
