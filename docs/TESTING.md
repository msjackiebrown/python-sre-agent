# Testing Strategy & Coverage

How to test the SRE Agent and run the test suite.

---

## Quick Start: Run All Tests

```bash
pytest tests/ -v
```

**Expected output:**
```
tests/test_db.py::test_yaml_parsing PASSED
tests/test_db.py::test_seed_runbooks PASSED
...
tests/test_tools.py::test_search_validation PASSED
...

================ 23 passed in 1.23s ================
```

---

## Test Structure

### Unit Tests: `tests/test_tools.py` (15 tests)

Test the business logic and validation layer **without** external dependencies.

```python
import pytest
from src.tools import search_runbooks, SearchRunbooksInput
from pydantic import ValidationError

def test_search_validation_min_length():
    """Query too short should fail."""
    with pytest.raises(ValidationError):
        search_runbooks(query="x")

def test_search_validation_max_length():
    """Query too long should fail."""
    with pytest.raises(ValidationError):
        search_runbooks(query="a" * 101)

def test_search_validation_max_results():
    """max_results > 20 should fail."""
    with pytest.raises(ValidationError):
        search_runbooks(query="database", max_results=50)
```

**What we test:**
- ✅ Input validation (Pydantic boundaries)
- ✅ Type coercion
- ✅ Error messages
- ✅ Edge cases (empty, whitespace, special chars)

**What we DON'T test:**
- ❌ Ollama connectivity
- ❌ ChromaDB search results
- ❌ Network calls

**Why:** Fast, reliable, no external dependencies.

### Integration Tests: `tests/test_db.py` (8 tests)

Test the data layer **with** real ChromaDB (but ephemeral).

```python
import pytest
from src.db import seed_runbooks, init_collection

def test_seed_runbooks_count():
    """Should load exactly 7 runbooks."""
    collection, count = seed_runbooks()
    assert count == 7

def test_search_finds_results():
    """Should find results for known keywords."""
    collection, _ = seed_runbooks()
    results = search_runbooks("database", max_results=3)
    assert "INCIDENT" in results
    assert len(results) > 0
```

**What we test:**
- ✅ File I/O (reading .md files)
- ✅ YAML frontmatter parsing
- ✅ Metadata extraction
- ✅ ChromaDB operations
- ✅ Vector similarity search

**What we DON'T test:**
- ❌ Ollama inference
- ❌ Full ReAct loop

**Why:** Deterministic, covers data pipeline.

### End-to-End Tests: `tests/test_agent.py` (Optional)

Test the full ReAct loop **with** running Ollama.

```python
import pytest
from src.agent import react_agent

@pytest.mark.slow
def test_react_loop_with_database_query():
    """Full agent loop: requires running Ollama."""
    response = react_agent("Database connection timeout")
    
    # Should have results
    assert "INCIDENT" in response or "Found" in response
    
    # Should not be an error
    assert "❌" not in response or "Error" in response
```

**What we test:**
- ✅ Full ReAct loop
- ✅ Tool calling integration
- ✅ LLM coordination
- ✅ Error handling

**What we DON'T test:**
- ❌ Individual tool logic (covered by unit tests)
- ❌ Ollama model quality (that's QA, not unit tests)

**Why:** Validates full system integration.

**Note:** Mark with `@pytest.mark.slow` and run separately:
```bash
pytest tests/test_agent.py -v --tb=short
# Requires: ollama serve running in another terminal
```

---

## Running Tests by Category

### Only Unit Tests (Fast)
```bash
pytest tests/test_tools.py -v
# ~0.5 seconds
# No dependencies needed
```

### Only Data Layer Tests (Fast)
```bash
pytest tests/test_db.py -v
# ~0.5 seconds
# Uses ephemeral ChromaDB
```

### Only Integration Tests
```bash
pytest tests/test_db.py tests/test_tools.py -v
# ~1 second
```

### Full Suite (Slow)
```bash
pytest tests/ -v
# ~2 seconds
# Skips test_agent.py unless you pass --slow
```

### With End-to-End Tests
```bash
# Start Ollama in another terminal: ollama serve

pytest tests/ --slow -v
# ~30-60 seconds (depends on inference speed)
```

---

## Test Coverage Report

### Current Coverage
```bash
pytest tests/ --cov=src --cov-report=html -v
# Generates htmlcov/index.html
```

**Expected results:**
- `src/db.py`: ~95% coverage (all public functions tested)
- `src/tools.py`: ~90% coverage (validation + tool logic)
- `src/agent.py`: ~70% coverage (requires running Ollama for full coverage)

### Coverage Targets
| Module | Target | Current | Notes |
|--------|--------|---------|-------|
| `db.py` | 95% | ✅ 95% | Data layer fully tested |
| `tools.py` | 90% | ✅ 90% | Validation + logic covered |
| `agent.py` | 70% | ✅ 70% | ReAct loop tested manually |

---

## Writing New Tests

### Template: Unit Test (Test Validation)

```python
import pytest
from pydantic import ValidationError
from src.tools import search_runbooks

def test_new_validation_rule():
    """Test a new validation boundary."""
    
    # Test the boundary
    with pytest.raises(ValidationError):
        search_runbooks(query="invalid")
    
    # Verify valid input works
    result = search_runbooks(query="valid query")
    assert isinstance(result, str)
```

**Best practices:**
- ✅ One assertion per test (or grouped by context)
- ✅ Use descriptive test names (`test_search_validation_min_length`)
- ✅ Include docstring explaining what and why
- ✅ Use `with pytest.raises(...)` for expected exceptions

### Template: Integration Test (Test Data Operations)

```python
import pytest
from src.db import seed_runbooks

def test_new_search_functionality():
    """Test new search feature with real data."""
    
    # Setup: Load data
    collection, count = seed_runbooks()
    assert count > 0
    
    # Test: Perform operation
    results = collection.query(
        query_texts=["new search term"],
        n_results=3
    )
    
    # Verify: Check results
    assert "ids" in results
    assert len(results["ids"]) <= 3
```

**Best practices:**
- ✅ Use fixtures for setup (see conftest.py)
- ✅ Test with real ephemeral data
- ✅ Clean up after tests (fixtures handle this)

---

## Fixtures: Shared Test Setup

### Available Fixtures (in `conftest.py`)

```python
@pytest.fixture
def collection():
    """Ephemeral ChromaDB collection for testing."""
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(name="test_runbooks")

@pytest.fixture
def seeded_collection():
    """Collection pre-loaded with sample runbooks."""
    collection, count = seed_runbooks()
    return collection
```

### Using Fixtures

```python
def test_search_with_fixture(seeded_collection):
    """Test search using pre-seeded collection."""
    results = seeded_collection.query(
        query_texts=["database"],
        n_results=3
    )
    assert len(results["ids"]) > 0
```

---

## Mocking: Testing Without External Services

### Mock Ollama for Agent Tests

```python
from unittest.mock import patch, MagicMock
from src.agent import react_agent

@patch("src.agent.chat")
def test_agent_without_ollama(mock_chat):
    """Test agent logic without running Ollama."""
    
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.message.content = "Agent response"
    mock_response.message.tool_calls = []
    mock_chat.return_value = mock_response
    
    # Test agent
    response = react_agent("Test query")
    
    # Verify LLM was called
    assert mock_chat.called
    assert response == "Agent response"
```

### Mock File I/O

```python
from unittest.mock import patch, mock_open

@patch("builtins.open", mock_open(read_data="---\nid: TEST\n---\nContent"))
def test_parse_runbook_without_files():
    """Test parsing without real files."""
    # Mocked open() returns our test data
```

---

## Continuous Integration (CI)

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest tests/ -v
      
      - name: Generate coverage
        run: pytest tests/ --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Performance Testing

### Timing Specific Tests

```bash
# Time how long tests take
pytest tests/ -v --durations=10

# Output:
# 10 slowest test durations
# test_agent.py::test_full_loop: 5.23s
# test_db.py::test_seed_runbooks: 0.34s
# ...
```

### Profiling Agent Speed

```python
import time
from src.agent import react_agent

start = time.time()
response = react_agent("Database timeout", verbose=False)
elapsed = time.time() - start

print(f"Agent response time: {elapsed:.2f}s")
```

**Expected:**
- With Ollama: 2-5 seconds (depends on model size and hardware)
- Without Ollama (mocked): <0.1 seconds

---

## Debugging Failed Tests

### Verbose Output
```bash
pytest tests/test_db.py::test_search_finds_results -vv
# -vv = extra verbose
```

### Print Debugging
```python
def test_something():
    result = search_runbooks("query")
    print(f"DEBUG: result = {result}")  # Will show in test output
    assert "something" in result
```

**Run with:**
```bash
pytest tests/ -v -s
# -s = show print statements
```

### Inspect Test Failures
```bash
# Stop on first failure
pytest tests/ -x

# Drop into debugger on failure
pytest tests/ --pdb

# Show full output
pytest tests/ -vv --tb=long
```

---

## Test Philosophy

### Why We Test Different Layers Differently

| Layer | Test Type | Why |
|-------|-----------|-----|
| **Business Logic** | Unit (mocked) | Fast, isolated, focus on logic |
| **Data Access** | Integration (real DB) | Test actual operations, deterministic |
| **Full System** | E2E (real Ollama) | Validate end-to-end, slow, optional |

### What NOT to Test

❌ **LLM reasoning quality** — That's QA, not unit testing
❌ **Ollama inference** — Out of scope for this project
❌ **Network connectivity** — Test only our error handling, not the network
❌ **Third-party libraries** — Trust that pydantic, chromadb, etc. work

---

## Troubleshooting Tests

### "ModuleNotFoundError"
```bash
# Make sure you're in the repo directory
cd python-sre-agent

# And install dependencies
pip install -r requirements.txt
```

### "Connection refused" in agent tests
```bash
# Make sure Ollama is running
ollama serve
# in another terminal
pytest tests/test_agent.py --slow
```

### Fixture issues
```bash
# Check conftest.py is in tests/ directory
ls tests/conftest.py

# Verify fixtures are imported
pytest tests/ --fixtures | grep seeded_collection
```

---

## See Also

- [GETTING_STARTED.md](./GETTING_STARTED.md) — Installation and usage
- [API.md](./API.md) — Programmatic API
- [ARCHITECTURE.md](./ARCHITECTURE.md) — System design
