"""Integration tests for the application.

These tests verify that different components work together correctly.
"""
import pytest
from unittest.mock import Mock, patch
from pages.utils import match_team_rules
from pages.settings.storage import DEFAULT_SETTINGS


class TestTeamsIntegration:
    """Integration tests for teams matching functionality."""

    def test_complex_team_matching_scenario(self):
        """Test realistic scenario with multiple teams and conditions."""
        teams_config = [
            {
                "name": "Data Engineering",
                "conditions": [
                    {"field": "job_name", "operator": "starts_with", "value": "data_"},
                    {"field": "tags", "operator": "has_key", "tag_key": "team", "logic": "OR"}
                ],
                "logic": "OR"
            },
            {
                "name": "ML Team",
                "conditions": [
                    {"field": "job_name", "operator": "contains", "value": "ml"},
                    {"field": "creator", "operator": "contains", "value": "ml-team", "logic": "AND"}
                ],
                "logic": "OR"
            },
            {
                "name": "Production",
                "conditions": [
                    {"field": "tags", "operator": "equals", "tag_key": "environment", "value": "prod"}
                ],
                "logic": "OR"
            }
        ]

        # Test case 1: Job matches Data Engineering (by name)
        result = match_team_rules(
            "data_pipeline_v2",
            "engineer@company.com",
            teams_config
        )
        assert "Data Engineering" in result

        # Test case 2: Job matches Data Engineering (by tag)
        result = match_team_rules(
            "etl_job",
            "engineer@company.com",
            teams_config,
            tags={"team": "data-eng"}
        )
        assert "Data Engineering" in result

        # Test case 3: Job matches ML Team (both conditions)
        result = match_team_rules(
            "train_ml_model",
            "ml-team@company.com",
            teams_config
        )
        assert "ML Team" in result

        # Test case 4: Job doesn't match ML Team (only one condition)
        result = match_team_rules(
            "train_ml_model",
            "other@company.com",
            teams_config
        )
        assert "ML Team" not in result

        # Test case 5: Job matches Production tag
        result = match_team_rules(
            "any_job",
            "user@company.com",
            teams_config,
            tags={"environment": "prod"}
        )
        assert "Production" in result

        # Test case 6: Job matches multiple teams
        result = match_team_rules(
            "data_ml_pipeline",
            "ml-team@company.com",
            teams_config,
            tags={"environment": "prod", "team": "ml"}
        )
        # Should match all three teams
        assert len(result) == 3
        assert set(result) == {"Data Engineering", "ML Team", "Production"}


class TestSettingsWorkflow:
    """Integration tests for settings workflow."""

    def test_default_settings_structure_is_valid(self):
        """Test that default settings have valid structure."""
        settings = DEFAULT_SETTINGS.copy()
        
        assert "version" in settings
        assert "timezone" in settings
        assert "teams" in settings
        assert isinstance(settings["teams"], list)

    def test_teams_config_compatibility(self):
        """Test that teams config works with match_team_rules."""
        # Create a settings-like teams config
        teams = [
            {
                "id": "team1",
                "name": "Test Team",
                "conditions": [
                    {"field": "job_name", "operator": "starts_with", "value": "test_"}
                ],
                "logic": "OR"
            }
        ]
        
        # Should work with match_team_rules
        result = match_team_rules("test_job", "user@example.com", teams)
        assert result == ["Test Team"]


class TestEndToEndScenarios:
    """End-to-end test scenarios simulating real usage."""

    def test_job_classification_workflow(self):
        """Test complete workflow of classifying jobs into teams."""
        # Setup: Company has 3 teams with different responsibilities
        teams_config = [
            {
                "name": "Platform Team",
                "conditions": [
                    {"field": "job_name", "operator": "starts_with", "value": "platform_"}
                ],
                "logic": "OR"
            },
            {
                "name": "Analytics Team",
                "conditions": [
                    {"field": "creator", "operator": "contains", "value": "analytics"}
                ],
                "logic": "OR"
            },
            {
                "name": "Critical Jobs",
                "conditions": [
                    {"field": "tags", "operator": "equals", "tag_key": "priority", "value": "critical"}
                ],
                "logic": "OR"
            }
        ]

        # Scenario: Multiple jobs need to be classified
        jobs = [
            {
                "name": "platform_monitoring",
                "creator": "devops@company.com",
                "tags": {}
            },
            {
                "name": "daily_report",
                "creator": "analytics@company.com",
                "tags": {"type": "report"}
            },
            {
                "name": "revenue_calculation",
                "creator": "analytics@company.com",
                "tags": {"priority": "critical"}
            },
        ]

        # Classify each job
        results = {}
        for job in jobs:
            matched = match_team_rules(
                job["name"],
                job["creator"],
                teams_config,
                job["tags"]
            )
            results[job["name"]] = matched

        # Verify classifications
        assert results["platform_monitoring"] == ["Platform Team"]
        assert results["daily_report"] == ["Analytics Team"]
        assert set(results["revenue_calculation"]) == {"Analytics Team", "Critical Jobs"}

    def test_empty_teams_edge_case(self):
        """Test system behavior with no teams configured."""
        result = match_team_rules("any_job", "any_creator", [])
        assert result == []

    def test_no_matching_teams(self):
        """Test when job doesn't match any team."""
        teams_config = [
            {
                "name": "Specific Team",
                "conditions": [
                    {"field": "job_name", "operator": "equals", "value": "specific_job"}
                ],
                "logic": "OR"
            }
        ]
        
        result = match_team_rules("other_job", "user@example.com", teams_config)
        assert result == []
