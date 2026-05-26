"""Tests for pages/utils.py module."""
import os
import pytest
from unittest.mock import patch, Mock
from pages.utils import match_team_rules, COMMON_TZ


class TestMatchTeamRules:
    """Tests for match_team_rules function."""

    def test_job_name_starts_with(self):
        """Test matching by job_name starts_with operator."""
        teams = [
            {
                "name": "Data Team",
                "conditions": [
                    {"field": "job_name", "operator": "starts_with", "value": "data_"}
                ],
                "logic": "OR"
            }
        ]
        result = match_team_rules("data_pipeline_prod", "user@example.com", teams)
        assert result == ["Data Team"]

    def test_job_name_ends_with(self):
        """Test matching by job_name ends_with operator."""
        teams = [
            {
                "name": "Prod Team",
                "conditions": [
                    {"field": "job_name", "operator": "ends_with", "value": "_prod"}
                ],
                "logic": "OR"
            }
        ]
        result = match_team_rules("etl_job_prod", "user@example.com", teams)
        assert result == ["Prod Team"]

    def test_job_name_contains(self):
        """Test matching by job_name contains operator."""
        teams = [
            {
                "name": "ETL Team",
                "conditions": [
                    {"field": "job_name", "operator": "contains", "value": "etl"}
                ],
                "logic": "OR"
            }
        ]
        result = match_team_rules("daily_etl_pipeline", "user@example.com", teams)
        assert result == ["ETL Team"]

    def test_job_name_equals(self):
        """Test matching by job_name equals operator."""
        teams = [
            {
                "name": "Special Job Team",
                "conditions": [
                    {"field": "job_name", "operator": "equals", "value": "important_job"}
                ],
                "logic": "OR"
            }
        ]
        result = match_team_rules("important_job", "user@example.com", teams)
        assert result == ["Special Job Team"]

    def test_creator_matching(self):
        """Test matching by creator field."""
        teams = [
            {
                "name": "ML Team",
                "conditions": [
                    {"field": "creator", "operator": "contains", "value": "ml-team"}
                ],
                "logic": "OR"
            }
        ]
        result = match_team_rules("any_job", "ml-team@example.com", teams)
        assert result == ["ML Team"]

    def test_tags_has_key(self):
        """Test matching by tags has_key operator."""
        teams = [
            {
                "name": "Tagged Team",
                "conditions": [
                    {"field": "tags", "operator": "has_key", "tag_key": "environment"}
                ],
                "logic": "OR"
            }
        ]
        tags = {"environment": "prod", "team": "data"}
        result = match_team_rules("job", "user@example.com", teams, tags)
        assert result == ["Tagged Team"]

    def test_tags_equals(self):
        """Test matching by tags equals operator."""
        teams = [
            {
                "name": "Prod Team",
                "conditions": [
                    {"field": "tags", "operator": "equals", "tag_key": "environment", "value": "prod"}
                ],
                "logic": "OR"
            }
        ]
        tags = {"environment": "prod"}
        result = match_team_rules("job", "user@example.com", teams, tags)
        assert result == ["Prod Team"]

    def test_tags_missing_key(self):
        """Test tags matching when key is missing."""
        teams = [
            {
                "name": "Prod Team",
                "conditions": [
                    {"field": "tags", "operator": "equals", "tag_key": "environment", "value": "prod"}
                ],
                "logic": "OR"
            }
        ]
        tags = {"team": "data"}  # missing 'environment' key
        result = match_team_rules("job", "user@example.com", teams, tags)
        assert result == []

    def test_and_logic(self):
        """Test multiple conditions with AND logic."""
        teams = [
            {
                "name": "Strict Team",
                "conditions": [
                    {"field": "job_name", "operator": "starts_with", "value": "data_"},
                    {"field": "creator", "operator": "contains", "value": "admin", "logic": "AND"}
                ],
                "logic": "OR"
            }
        ]
        # Should match
        result = match_team_rules("data_pipeline", "admin@example.com", teams)
        assert result == ["Strict Team"]
        
        # Should not match (only one condition satisfied)
        result = match_team_rules("data_pipeline", "user@example.com", teams)
        assert result == []

    def test_or_logic(self):
        """Test multiple conditions with OR logic."""
        teams = [
            {
                "name": "Flexible Team",
                "conditions": [
                    {"field": "job_name", "operator": "starts_with", "value": "data_"},
                    {"field": "job_name", "operator": "starts_with", "value": "ml_", "logic": "OR"}
                ],
                "logic": "OR"
            }
        ]
        result1 = match_team_rules("data_pipeline", "user@example.com", teams)
        result2 = match_team_rules("ml_model", "user@example.com", teams)
        assert result1 == ["Flexible Team"]
        assert result2 == ["Flexible Team"]

    def test_multiple_teams_match(self):
        """Test that a job can match multiple teams."""
        teams = [
            {
                "name": "Team A",
                "conditions": [
                    {"field": "job_name", "operator": "contains", "value": "pipeline"}
                ],
                "logic": "OR"
            },
            {
                "name": "Team B",
                "conditions": [
                    {"field": "job_name", "operator": "starts_with", "value": "data"}
                ],
                "logic": "OR"
            }
        ]
        result = match_team_rules("data_pipeline", "user@example.com", teams)
        assert set(result) == {"Team A", "Team B"}

    def test_no_match(self):
        """Test when no teams match."""
        teams = [
            {
                "name": "Team A",
                "conditions": [
                    {"field": "job_name", "operator": "starts_with", "value": "specific_"}
                ],
                "logic": "OR"
            }
        ]
        result = match_team_rules("other_job", "user@example.com", teams)
        assert result == []

    def test_empty_teams_config(self):
        """Test with empty teams configuration."""
        result = match_team_rules("job", "user@example.com", [])
        assert result == []

    def test_team_without_conditions(self):
        """Test team without conditions is skipped."""
        teams = [
            {
                "name": "Team A",
                "conditions": []
            }
        ]
        result = match_team_rules("job", "user@example.com", teams)
        assert result == []

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        teams = [
            {
                "name": "Team A",
                "conditions": [
                    {"field": "job_name", "operator": "contains", "value": "PIPELINE"}
                ],
                "logic": "OR"
            }
        ]
        result = match_team_rules("data_pipeline_prod", "user@example.com", teams)
        assert result == ["Team A"]


class TestCommonTZ:
    """Tests for COMMON_TZ constant."""

    def test_common_tz_contains_utc(self):
        """Test that COMMON_TZ includes UTC."""
        assert "UTC" in COMMON_TZ

    def test_common_tz_contains_major_zones(self):
        """Test that COMMON_TZ includes major timezones."""
        expected_zones = ["UTC", "US/Eastern", "US/Pacific", "Europe/London"]
        for zone in expected_zones:
            assert zone in COMMON_TZ
