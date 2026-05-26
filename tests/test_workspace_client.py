"""Tests for WorkspaceClient initialization."""
import os
import pytest
from unittest.mock import patch, Mock, MagicMock
from pages.utils import make_workspace_client


class TestMakeWorkspaceClient:
    """Tests for make_workspace_client function."""
    
    @patch('pages.utils.WorkspaceClient')
    def test_with_user_token_and_host(self, mock_ws_client, monkeypatch):
        """Test client creation with user token."""
        monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
        monkeypatch.setenv("DATABRICKS_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "test_secret")
        
        mock_instance = Mock()
        mock_ws_client.return_value = mock_instance
        
        result = make_workspace_client(user_token="user_token_123")
        
        # Should call WorkspaceClient with host and token
        mock_ws_client.assert_called_once_with(
            host="https://test.databricks.com",
            token="user_token_123"
        )
        assert result == mock_instance
        
        # Should restore CLIENT_ID and CLIENT_SECRET after
        assert os.getenv("DATABRICKS_CLIENT_ID") == "test_client_id"
        assert os.getenv("DATABRICKS_CLIENT_SECRET") == "test_secret"
    
    @patch('pages.utils.WorkspaceClient')
    def test_with_user_token_restores_env_vars(self, mock_ws_client, monkeypatch):
        """Test that environment variables are restored even on exception."""
        monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
        monkeypatch.setenv("DATABRICKS_CLIENT_ID", "original_id")
        monkeypatch.setenv("DATABRICKS_CLIENT_SECRET", "original_secret")
        
        mock_ws_client.side_effect = Exception("Connection error")
        
        with pytest.raises(Exception):
            make_workspace_client(user_token="user_token_123")
        
        # Environment variables should be restored
        assert os.getenv("DATABRICKS_CLIENT_ID") == "original_id"
        assert os.getenv("DATABRICKS_CLIENT_SECRET") == "original_secret"
    
    @patch('pages.utils.WorkspaceClient')
    def test_with_client_id(self, mock_ws_client, monkeypatch):
        """Test client creation with OAuth (CLIENT_ID)."""
        monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
        monkeypatch.setenv("DATABRICKS_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("DATABRICKS_TOKEN", "should_be_removed")
        
        mock_instance = Mock()
        mock_ws_client.return_value = mock_instance
        
        result = make_workspace_client()
        
        # Should call WorkspaceClient without arguments (uses env vars)
        mock_ws_client.assert_called_once_with()
        assert result == mock_instance
        
        # Should restore DATABRICKS_TOKEN after
        assert os.getenv("DATABRICKS_TOKEN") == "should_be_removed"
    
    @patch('pages.utils.WorkspaceClient')
    def test_with_client_id_restores_token(self, mock_ws_client, monkeypatch):
        """Test that DATABRICKS_TOKEN is restored even on exception."""
        monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
        monkeypatch.setenv("DATABRICKS_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("DATABRICKS_TOKEN", "original_token")
        
        mock_ws_client.side_effect = Exception("OAuth error")
        
        with pytest.raises(Exception):
            make_workspace_client()
        
        # Token should be restored
        assert os.getenv("DATABRICKS_TOKEN") == "original_token"
    
    @patch('pages.utils.WorkspaceClient')
    def test_with_token_env_var(self, mock_ws_client, monkeypatch):
        """Test client creation with DATABRICKS_TOKEN env var."""
        monkeypatch.setenv("DATABRICKS_TOKEN", "env_token_123")
        monkeypatch.delenv("DATABRICKS_HOST", raising=False)
        monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
        
        mock_instance = Mock()
        mock_ws_client.return_value = mock_instance
        
        result = make_workspace_client()
        
        # Should call WorkspaceClient without arguments (uses DATABRICKS_TOKEN from env)
        mock_ws_client.assert_called_once_with()
        assert result == mock_instance
    
    @patch('pages.utils.WorkspaceClient')
    def test_with_profile_fallback(self, mock_ws_client, monkeypatch):
        """Test fallback to DEFAULT profile."""
        # Remove all relevant env vars
        monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
        monkeypatch.delenv("DATABRICKS_HOST", raising=False)
        monkeypatch.delenv("DATABRICKS_CLIENT_ID", raising=False)
        
        mock_instance = Mock()
        mock_ws_client.return_value = mock_instance
        
        result = make_workspace_client()
        
        # Should call WorkspaceClient with profile
        mock_ws_client.assert_called_once_with(profile="DEFAULT")
        assert result == mock_instance
    
    @patch('pages.utils.WorkspaceClient')
    def test_priority_user_token_over_client_id(self, mock_ws_client, monkeypatch):
        """Test that user_token takes priority over CLIENT_ID."""
        monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
        monkeypatch.setenv("DATABRICKS_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("DATABRICKS_TOKEN", "env_token")
        
        mock_instance = Mock()
        mock_ws_client.return_value = mock_instance
        
        result = make_workspace_client(user_token="user_token_priority")
        
        # Should use user_token, not CLIENT_ID or env token
        mock_ws_client.assert_called_once_with(
            host="https://test.databricks.com",
            token="user_token_priority"
        )
        assert result == mock_instance
    
    @patch('pages.utils.WorkspaceClient')
    def test_no_host_with_user_token(self, mock_ws_client, monkeypatch):
        """Test that user_token is ignored if no host is set."""
        monkeypatch.delenv("DATABRICKS_HOST", raising=False)
        monkeypatch.setenv("DATABRICKS_TOKEN", "env_token")
        
        mock_instance = Mock()
        mock_ws_client.return_value = mock_instance
        
        result = make_workspace_client(user_token="user_token")
        
        # Should fall back to env token (not use user_token without host)
        mock_ws_client.assert_called_once_with()
        assert result == mock_instance
