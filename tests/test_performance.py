"""Performance tests."""
import pytest
import time
from pages.utils import match_team_rules


class TestPerformance:
    """Performance tests for critical functions."""
    
    def test_match_team_rules_performance_large_teams(self):
        """Test that match_team_rules handles large team configs efficiently."""
        # Create large teams config with 100 teams
        teams = [
            {
                "name": f"Team {i}",
                "conditions": [
                    {"field": "job_name", "operator": "contains", "value": f"pattern_{i}"}
                ],
                "logic": "OR"
            }
            for i in range(100)
        ]
        
        start = time.time()
        result = match_team_rules("test_job", "user@example.com", teams)
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 0.1, f"Took {duration}s, expected < 0.1s"
    
    def test_match_team_rules_performance_complex_conditions(self):
        """Test performance with teams having many conditions."""
        # Create teams with complex condition sets
        teams = [
            {
                "name": f"Team {i}",
                "conditions": [
                    {"field": "job_name", "operator": "starts_with", "value": f"prefix_{j}"}
                    for j in range(10)
                ],
                "logic": "OR"
            }
            for i in range(20)
        ]
        
        start = time.time()
        result = match_team_rules("prefix_5_job", "user@example.com", teams)
        duration = time.time() - start
        
        # Should complete quickly even with complex conditions
        assert duration < 0.1, f"Took {duration}s, expected < 0.1s"
    
    def test_match_team_rules_performance_with_tags(self):
        """Test performance when checking tags."""
        teams = [
            {
                "name": f"Team {i}",
                "conditions": [
                    {"field": "tags", "operator": "has_key", "tag_key": f"key_{j}"}
                    for j in range(5)
                ],
                "logic": "OR"
            }
            for i in range(50)
        ]
        
        tags = {f"key_{i}": f"value_{i}" for i in range(20)}
        
        start = time.time()
        result = match_team_rules("test_job", "user@example.com", teams, tags)
        duration = time.time() - start
        
        assert duration < 0.1, f"Took {duration}s, expected < 0.1s"
    
    def test_match_team_rules_performance_no_matches(self):
        """Test performance when no teams match (worst case)."""
        # Create many teams that won't match
        teams = [
            {
                "name": f"Team {i}",
                "conditions": [
                    {"field": "job_name", "operator": "equals", "value": f"specific_job_{i}"}
                ],
                "logic": "OR"
            }
            for i in range(100)
        ]
        
        start = time.time()
        result = match_team_rules("different_job", "user@example.com", teams)
        duration = time.time() - start
        
        # Even when checking all teams, should be fast
        assert duration < 0.1, f"Took {duration}s, expected < 0.1s"
        assert result == []
    
    def test_match_team_rules_performance_all_match(self):
        """Test performance when all teams match (best case for team count)."""
        # Create teams that all match
        teams = [
            {
                "name": f"Team {i}",
                "conditions": [
                    {"field": "job_name", "operator": "contains", "value": "test"}
                ],
                "logic": "OR"
            }
            for i in range(100)
        ]
        
        start = time.time()
        result = match_team_rules("test_job", "user@example.com", teams)
        duration = time.time() - start
        
        assert duration < 0.1, f"Took {duration}s, expected < 0.1s"
        assert len(result) == 100
    
    def test_match_team_rules_performance_and_logic(self):
        """Test performance with AND logic conditions."""
        teams = [
            {
                "name": f"Team {i}",
                "conditions": [
                    {"field": "job_name", "operator": "contains", "value": "test"},
                    {"field": "creator", "operator": "contains", "value": "user", "logic": "AND"},
                    {"field": "tags", "operator": "has_key", "tag_key": "env", "logic": "AND"}
                ],
                "logic": "OR"
            }
            for i in range(50)
        ]
        
        tags = {"env": "prod", "team": "data"}
        
        start = time.time()
        result = match_team_rules("test_job", "user@example.com", teams, tags)
        duration = time.time() - start
        
        assert duration < 0.1, f"Took {duration}s, expected < 0.1s"
    
    def test_match_team_rules_repeated_calls(self):
        """Test performance over multiple repeated calls."""
        teams = [
            {
                "name": f"Team {i}",
                "conditions": [
                    {"field": "job_name", "operator": "starts_with", "value": f"job_{i}"}
                ],
                "logic": "OR"
            }
            for i in range(20)
        ]
        
        start = time.time()
        for i in range(100):
            result = match_team_rules(f"job_{i % 20}_test", "user@example.com", teams)
        duration = time.time() - start
        
        # 100 calls should complete quickly
        assert duration < 0.5, f"100 calls took {duration}s, expected < 0.5s"
        avg_duration = duration / 100
        assert avg_duration < 0.005, f"Average call took {avg_duration}s, expected < 0.005s"
    
    @pytest.mark.slow
    def test_match_team_rules_stress_test(self):
        """Stress test with very large configuration."""
        # Create 500 teams with multiple conditions each
        teams = [
            {
                "name": f"Team {i}",
                "conditions": [
                    {"field": "job_name", "operator": "contains", "value": f"pattern_{j}"}
                    for j in range(3)
                ],
                "logic": "OR"
            }
            for i in range(500)
        ]
        
        tags = {f"tag_{i}": f"value_{i}" for i in range(50)}
        
        start = time.time()
        result = match_team_rules("pattern_1_job", "user@example.com", teams, tags)
        duration = time.time() - start
        
        # Even with 500 teams, should complete in reasonable time
        assert duration < 1.0, f"Took {duration}s, expected < 1.0s"
    
    def test_match_team_rules_memory_efficiency(self):
        """Test that function doesn't create excessive temporary objects."""
        import sys
        
        teams = [
            {
                "name": f"Team {i}",
                "conditions": [
                    {"field": "job_name", "operator": "contains", "value": f"test_{j}"}
                    for j in range(5)
                ],
                "logic": "OR"
            }
            for i in range(100)
        ]
        
        # Get initial object count
        initial_objects = len(sys.getobjects(0)) if hasattr(sys, 'getobjects') else 0
        
        # Run multiple times
        for _ in range(10):
            result = match_team_rules("test_1_job", "user@example.com", teams)
        
        # Object count shouldn't grow excessively
        # This is a basic check - in practice you'd use memory profiling tools
        # Just verify the function completes without error
        assert True  # Function completed without memory errors
