"""Tests for data validation."""
import pytest
from typing import Any


def validate_team_config(team_config: dict) -> tuple[bool, str]:
    """Validate a team configuration dictionary.
    
    Returns:
        (is_valid, error_message)
    """
    if not isinstance(team_config, dict):
        return False, "Team config must be a dictionary"
    
    # Check required fields
    if "name" not in team_config:
        return False, "Missing required field: name"
    
    if not team_config["name"] or not isinstance(team_config["name"], str):
        return False, "Field 'name' must be a non-empty string"
    
    if "conditions" not in team_config:
        return False, "Missing required field: conditions"
    
    if not isinstance(team_config["conditions"], list):
        return False, "Field 'conditions' must be a list"
    
    # Validate logic field if present
    if "logic" in team_config:
        if team_config["logic"] not in ["AND", "OR"]:
            return False, "Field 'logic' must be 'AND' or 'OR'"
    
    # Validate each condition
    valid_operators = ["starts_with", "ends_with", "contains", "equals", "has_key"]
    valid_fields = ["job_name", "creator", "tags"]
    
    for i, condition in enumerate(team_config["conditions"]):
        if not isinstance(condition, dict):
            return False, f"Condition {i} must be a dictionary"
        
        if "field" not in condition:
            return False, f"Condition {i} missing required field: field"
        
        if condition["field"] not in valid_fields:
            return False, f"Condition {i} has invalid field '{condition['field']}'. Must be one of {valid_fields}"
        
        if "operator" not in condition:
            return False, f"Condition {i} missing required field: operator"
        
        if condition["operator"] not in valid_operators:
            return False, f"Condition {i} has invalid operator '{condition['operator']}'. Must be one of {valid_operators}"
        
        # Tags field requires tag_key
        if condition["field"] == "tags":
            if condition["operator"] != "has_key" and "tag_key" not in condition:
                return False, f"Condition {i} with tags field requires 'tag_key'"
        
        # Non-has_key operators require value
        if condition["operator"] != "has_key" and "value" not in condition:
            return False, f"Condition {i} with operator '{condition['operator']}' requires 'value'"
        
        # Validate logic in condition
        if "logic" in condition and condition["logic"] not in ["AND", "OR"]:
            return False, f"Condition {i} has invalid logic '{condition['logic']}'. Must be 'AND' or 'OR'"
    
    return True, ""


class TestTeamsConfigValidation:
    """Tests for teams configuration validation."""
    
    def test_valid_team_config(self):
        """Test that valid config passes validation."""
        config = {
            "name": "Data Team",
            "conditions": [
                {
                    "field": "job_name",
                    "operator": "starts_with",
                    "value": "data_"
                }
            ],
            "logic": "OR"
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is True
        assert error == ""
    
    def test_valid_complex_config(self):
        """Test complex valid configuration."""
        config = {
            "name": "ML Team",
            "conditions": [
                {
                    "field": "job_name",
                    "operator": "contains",
                    "value": "ml"
                },
                {
                    "field": "creator",
                    "operator": "equals",
                    "value": "ml-team@example.com",
                    "logic": "AND"
                },
                {
                    "field": "tags",
                    "operator": "has_key",
                    "tag_key": "environment",
                    "logic": "OR"
                }
            ],
            "logic": "OR"
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is True
        assert error == ""
    
    def test_not_a_dict(self):
        """Test that non-dict config fails validation."""
        config = ["not", "a", "dict"]
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "must be a dictionary" in error
    
    def test_missing_name(self):
        """Test that missing name fails validation."""
        config = {
            "conditions": [
                {"field": "job_name", "operator": "contains", "value": "test"}
            ]
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "name" in error
    
    def test_empty_name(self):
        """Test that empty name fails validation."""
        config = {
            "name": "",
            "conditions": []
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "non-empty string" in error
    
    def test_missing_conditions(self):
        """Test that missing conditions fails validation."""
        config = {
            "name": "Test Team"
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "conditions" in error
    
    def test_conditions_not_list(self):
        """Test that non-list conditions fails validation."""
        config = {
            "name": "Test Team",
            "conditions": "not a list"
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "must be a list" in error
    
    def test_invalid_logic(self):
        """Test that invalid logic value fails validation."""
        config = {
            "name": "Test Team",
            "conditions": [],
            "logic": "XOR"
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "logic" in error.lower()
        assert "AND" in error and "OR" in error
    
    def test_invalid_operator(self):
        """Test that invalid operator is rejected."""
        config = {
            "name": "Test Team",
            "conditions": [
                {
                    "field": "job_name",
                    "operator": "regex_match",
                    "value": ".*test.*"
                }
            ]
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "invalid operator" in error.lower()
        assert "regex_match" in error
    
    def test_invalid_field(self):
        """Test that invalid field is rejected."""
        config = {
            "name": "Test Team",
            "conditions": [
                {
                    "field": "job_type",
                    "operator": "equals",
                    "value": "scheduled"
                }
            ]
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "invalid field" in error.lower()
        assert "job_type" in error
    
    def test_missing_required_fields(self):
        """Test that missing required fields in condition are rejected."""
        config = {
            "name": "Test Team",
            "conditions": [
                {
                    "operator": "contains",
                    "value": "test"
                }
            ]
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "field" in error.lower()
    
    def test_missing_value_for_non_has_key_operator(self):
        """Test that value is required for non-has_key operators."""
        config = {
            "name": "Test Team",
            "conditions": [
                {
                    "field": "job_name",
                    "operator": "contains"
                }
            ]
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "value" in error.lower()
    
    def test_tags_operator_requires_tag_key(self):
        """Test that tags operators (except has_key) require tag_key."""
        config = {
            "name": "Test Team",
            "conditions": [
                {
                    "field": "tags",
                    "operator": "equals",
                    "value": "prod"
                }
            ]
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "tag_key" in error.lower()
    
    def test_tags_has_key_valid_without_value(self):
        """Test that has_key operator doesn't require value."""
        config = {
            "name": "Test Team",
            "conditions": [
                {
                    "field": "tags",
                    "operator": "has_key",
                    "tag_key": "environment"
                }
            ]
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is True
        assert error == ""
    
    def test_condition_not_dict(self):
        """Test that non-dict condition fails validation."""
        config = {
            "name": "Test Team",
            "conditions": [
                "not a dict"
            ]
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is False
        assert "must be a dictionary" in error
    
    def test_empty_conditions_list(self):
        """Test that empty conditions list is valid."""
        config = {
            "name": "Test Team",
            "conditions": []
        }
        
        is_valid, error = validate_team_config(config)
        
        assert is_valid is True
        assert error == ""
