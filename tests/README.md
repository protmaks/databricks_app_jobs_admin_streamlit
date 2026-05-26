# Tests

Test coverage for Databricks Admin App.

## Test Structure

```
tests/
├── __init__.py                 # Test package
├── conftest.py                 # Common pytest fixtures
├── test_utils.py               # Tests for pages/utils.py (17 tests)
├── test_storage.py             # Tests for pages/settings/storage.py (13 tests)
├── test_integration.py         # Integration tests (6 tests)
├── test_workspace_client.py    # Tests for WorkspaceClient initialization (8 tests)
├── test_user_prefs.py          # Tests for user preferences (15 tests)
├── test_validation.py          # Tests for config validation (16 tests)
├── test_performance.py         # Performance tests (9 tests)
└── README.md                   # This file
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_utils.py
```

### Run specific test
```bash
pytest tests/test_utils.py::TestMatchTeamRules::test_job_name_starts_with
```

### Run with code coverage
```bash
pytest --cov=pages --cov-report=html
```

### Run only fast tests (without integration tests)
```bash
pytest -m "not integration"
```

## Coverage

### test_utils.py (17 tests)
- **match_team_rules()** - complete coverage of all operators and logic
  - starts_with, ends_with, contains, equals
  - All field types: job_name, creator, tags
  - AND/OR logic
  - Multiple matches
  - No match cases
  - Case-insensitive matching
  
- **COMMON_TZ** - constant validation

### test_storage.py (13 tests)
- **load_settings()** - loading settings
- **save_settings()** - saving settings
- **_migrate()** - data migration
- **_ws_read()** / **_ws_write()** - Workspace Files operations
- Fallback to local files
- Error handling

### test_integration.py (6 tests)
- Complex team matching scenarios
- Working with multiple teams
- End-to-end job classification scenarios
- Edge cases (empty configs, no matches)

### test_workspace_client.py (8 tests)
- **make_workspace_client()** - all authentication methods
- User token with host
- OAuth with CLIENT_ID
- Token environment variable
- Profile fallback
- Environment variable restoration on errors
- Priority ordering of authentication methods

### test_user_prefs.py (15 tests)
- **load_user_prefs()** / **save_user_prefs()** - user preferences
- Username extraction and sanitization
- Workspace Files and local file operations
- User isolation (different users have separate prefs)
- Error handling and fallback mechanisms

### test_validation.py (16 tests)
- **validate_team_config()** - teams configuration validation
- All required fields validation
- Valid and invalid operators
- Valid and invalid field types
- Logic validation (AND/OR)
- Condition structure validation
- Tags-specific validation rules

### test_performance.py (9 tests)
- **match_team_rules()** performance tests
- Large team configurations (100+ teams)
- Complex conditions (multiple conditions per team)
- Tags processing performance
- Best and worst case scenarios
- Repeated calls performance
- Stress tests (500 teams)
- Memory efficiency

## Implemented Tests Summary

**Total: 84 tests**
- All tests passing
- 100% success rate
- No TODO items remaining

## Fixtures

### conftest.py provides:
- `mock_workspace_client` - mock Databricks WorkspaceClient
- `sample_settings` - sample settings configuration
- `sample_user_prefs` - sample user preferences
- `temp_test_dir` - temporary directory for file operations
- `mock_env_vars` - automatic environment variables mock

## Best Practices

1. **Test isolation** - each test is independent and doesn't affect others
2. **Mocking** - use mocks for external dependencies (Databricks API)
3. **Fixture reuse** - common fixtures in conftest.py
4. **Descriptive names** - tests should be self-documenting
5. **Arrange-Act-Assert** - structure for each test
6. **Coverage** - aim for >80% coverage of critical code

## CI/CD

To integrate into CI/CD, add to `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=pages --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Troubleshooting

### ImportError when running tests
```bash
# Install package in dev mode
pip install -e .
```

### Tests fail due to environment variables
- Check that `.env` file exists or use `mock_env_vars` fixture

### Slow tests
```bash
# Run only unit tests
pytest -m "not integration"
```
