"""Tests for user preferences storage."""
import json
import base64
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from databricks.sdk.service.workspace import ExportFormat
from pages.settings.storage import (
    load_user_prefs,
    save_user_prefs,
    _get_username,
    _user_prefs_ws_path,
    _user_prefs_local_path,
)


class TestGetUsername:
    """Tests for _get_username function."""
    
    def test_get_username_from_user_name(self, mock_workspace_client):
        """Test getting username from user_name field."""
        mock_user = Mock()
        mock_user.user_name = "user@example.com"
        mock_user.display_name = "User Name"
        mock_workspace_client.current_user.me.return_value = mock_user
        
        result = _get_username(mock_workspace_client)
        
        assert result == "user@example.com"
    
    def test_get_username_from_display_name(self, mock_workspace_client):
        """Test getting username from display_name when user_name is None."""
        mock_user = Mock()
        mock_user.user_name = None
        mock_user.display_name = "User Name"
        mock_workspace_client.current_user.me.return_value = mock_user
        
        result = _get_username(mock_workspace_client)
        
        assert result == "User_Name"  # Spaces replaced with underscore
    
    def test_get_username_sanitization(self, mock_workspace_client):
        """Test that special characters are sanitized."""
        mock_user = Mock()
        mock_user.user_name = "user+test@example.com"
        mock_user.display_name = None
        mock_workspace_client.current_user.me.return_value = mock_user
        
        result = _get_username(mock_workspace_client)
        
        assert result == "user_test@example.com"  # + replaced with _
    
    def test_get_username_fallback_on_error(self, mock_workspace_client):
        """Test fallback to 'default' when API call fails."""
        mock_workspace_client.current_user.me.side_effect = Exception("API error")
        
        result = _get_username(mock_workspace_client)
        
        assert result == "default"
    
    def test_get_username_fallback_when_both_none(self, mock_workspace_client):
        """Test fallback to 'default' when both fields are None."""
        mock_user = Mock()
        mock_user.user_name = None
        mock_user.display_name = None
        mock_workspace_client.current_user.me.return_value = mock_user
        
        result = _get_username(mock_workspace_client)
        
        assert result == "default"


class TestUserPrefsPath:
    """Tests for user prefs path functions."""
    
    def test_user_prefs_ws_path(self, mock_workspace_client):
        """Test workspace path generation."""
        mock_user = Mock()
        mock_user.user_name = "test@example.com"
        mock_user.display_name = None
        mock_workspace_client.current_user.me.return_value = mock_user
        
        result = _user_prefs_ws_path(mock_workspace_client)
        
        assert result == "/Shared/databricks_admin_app/user_prefs/test@example.com.json"
    
    def test_user_prefs_local_path(self, mock_workspace_client, tmp_path, monkeypatch):
        """Test local path generation."""
        mock_user = Mock()
        mock_user.user_name = "test@example.com"
        mock_user.display_name = None
        mock_workspace_client.current_user.me.return_value = mock_user
        
        # Mock _LOCAL_USER_PREFS_DIR
        test_dir = tmp_path / "user_prefs_local"
        with patch("pages.settings.storage._LOCAL_USER_PREFS_DIR", test_dir):
            result = _user_prefs_local_path(mock_workspace_client)
            
            assert result == test_dir / "test@example.com.json"
            assert test_dir.exists()  # Should create directory


class TestLoadUserPrefs:
    """Tests for load_user_prefs function."""
    
    def test_load_from_workspace(self, mock_workspace_client):
        """Test loading user preferences from workspace."""
        prefs_data = {"default_teams": ["team1"], "last_timezone": "US/Pacific"}
        mock_response = Mock()
        mock_response.content = base64.b64encode(
            json.dumps(prefs_data).encode("utf-8")
        ).decode("ascii")
        mock_workspace_client.workspace.export.return_value = mock_response
        
        mock_user = Mock()
        mock_user.user_name = "test@example.com"
        mock_user.display_name = None
        mock_workspace_client.current_user.me.return_value = mock_user
        
        result = load_user_prefs(mock_workspace_client)
        
        assert result == prefs_data
        mock_workspace_client.workspace.export.assert_called_once()
    
    def test_load_returns_empty_dict_when_not_dict(self, mock_workspace_client):
        """Test that non-dict data returns empty dict."""
        mock_response = Mock()
        mock_response.content = base64.b64encode(b'[]').decode("ascii")
        mock_workspace_client.workspace.export.return_value = mock_response
        
        mock_user = Mock()
        mock_user.user_name = "test@example.com"
        mock_user.display_name = None
        mock_workspace_client.current_user.me.return_value = mock_user
        
        result = load_user_prefs(mock_workspace_client)
        
        assert result == {}
    
    @patch("pages.settings.storage._user_prefs_local_path")
    def test_load_fallback_to_local(self, mock_local_path, mock_workspace_client, tmp_path):
        """Test fallback to local file when workspace read fails."""
        # Workspace read fails
        mock_workspace_client.workspace.export.side_effect = Exception("Network error")
        
        # Local file exists
        local_file = tmp_path / "test_user.json"
        prefs_data = {"default_teams": ["team2"]}
        local_file.write_text(json.dumps(prefs_data))
        mock_local_path.return_value = local_file
        
        result = load_user_prefs(mock_workspace_client)
        
        assert result == prefs_data
    
    @patch("pages.settings.storage._user_prefs_local_path")
    def test_load_returns_empty_dict_on_all_failures(self, mock_local_path, mock_workspace_client):
        """Test that empty dict is returned when both sources fail."""
        mock_workspace_client.workspace.export.side_effect = Exception("WS error")
        mock_local_path.return_value.read_text.side_effect = Exception("Local error")
        
        result = load_user_prefs(mock_workspace_client)
        
        assert result == {}


class TestSaveUserPrefs:
    """Tests for save_user_prefs function."""
    
    def test_save_to_workspace(self, mock_workspace_client):
        """Test saving user preferences to workspace."""
        prefs = {"default_teams": ["team1"], "last_timezone": "US/Pacific"}
        
        mock_user = Mock()
        mock_user.user_name = "test@example.com"
        mock_user.display_name = None
        mock_workspace_client.current_user.me.return_value = mock_user
        
        save_user_prefs(mock_workspace_client, prefs)
        
        # Should call import_ once
        mock_workspace_client.workspace.import_.assert_called_once()
        call_args = mock_workspace_client.workspace.import_.call_args
        assert "/Shared/databricks_admin_app/user_prefs/test@example.com.json" in call_args.kwargs["path"]
    
    @patch("pages.settings.storage._user_prefs_local_path")
    def test_save_fallback_to_local(self, mock_local_path, mock_workspace_client, tmp_path):
        """Test fallback to local file when workspace write fails."""
        mock_workspace_client.workspace.import_.side_effect = Exception("Permission denied")
        
        local_file = tmp_path / "test_user.json"
        mock_local_path.return_value = local_file
        
        prefs = {"default_teams": ["team3"]}
        save_user_prefs(mock_workspace_client, prefs)
        
        # Should save to local file
        assert local_file.exists()
        saved_data = json.loads(local_file.read_text())
        assert saved_data == prefs
    
    @patch("pages.settings.storage._user_prefs_local_path")
    def test_save_raises_when_both_fail(self, mock_local_path, mock_workspace_client):
        """Test that RuntimeError is raised when both saves fail."""
        mock_workspace_client.workspace.import_.side_effect = Exception("WS error")
        mock_local_path.return_value.write_text.side_effect = Exception("Local error")
        
        prefs = {"default_teams": ["team1"]}
        
        with pytest.raises(RuntimeError) as exc_info:
            save_user_prefs(mock_workspace_client, prefs)
        
        assert "Failed to save user prefs" in str(exc_info.value)


class TestUserPrefsIsolation:
    """Tests for user preferences isolation."""
    
    @patch("pages.settings.storage._user_prefs_local_path")
    def test_different_users_have_different_prefs(self, mock_local_path, tmp_path):
        """Test that different users have isolated preferences."""
        # User 1
        mock_client_1 = Mock()
        mock_user_1 = Mock()
        mock_user_1.user_name = "user1@example.com"
        mock_user_1.display_name = None
        mock_client_1.current_user.me.return_value = mock_user_1
        mock_client_1.workspace.import_.return_value = None
        
        # User 2
        mock_client_2 = Mock()
        mock_user_2 = Mock()
        mock_user_2.user_name = "user2@example.com"
        mock_user_2.display_name = None
        mock_client_2.current_user.me.return_value = mock_user_2
        mock_client_2.workspace.import_.return_value = None
        
        # Setup local paths
        user1_file = tmp_path / "user1@example.com.json"
        user2_file = tmp_path / "user2@example.com.json"
        
        def local_path_side_effect(w):
            if w == mock_client_1:
                return user1_file
            else:
                return user2_file
        
        mock_local_path.side_effect = local_path_side_effect
        
        # Save different prefs for each user
        prefs_1 = {"default_teams": ["team1"]}
        prefs_2 = {"default_teams": ["team2", "team3"]}
        
        # Both clients fail workspace write, should use local
        mock_client_1.workspace.import_.side_effect = Exception("WS error")
        mock_client_2.workspace.import_.side_effect = Exception("WS error")
        
        save_user_prefs(mock_client_1, prefs_1)
        save_user_prefs(mock_client_2, prefs_2)
        
        # Verify files are different
        assert user1_file.exists()
        assert user2_file.exists()
        
        saved_1 = json.loads(user1_file.read_text())
        saved_2 = json.loads(user2_file.read_text())
        
        assert saved_1 == prefs_1
        assert saved_2 == prefs_2
        assert saved_1 != saved_2
