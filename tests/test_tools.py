"""Tests for src/tools.py — Tool validation and ChromaDB integration."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic import ValidationError
from tools import SearchRunbooksInput, search_runbooks


# ─────────────────────────────────────────────
# Test 1: SearchRunbooksInput Validation
# ─────────────────────────────────────────────

def test_search_runbooks_input_valid():
    """SearchRunbooksInput should accept valid query and max_results."""
    validated = SearchRunbooksInput(query="database timeout", max_results=5)
    assert validated.query == "database timeout"
    assert validated.max_results == 5


def test_search_runbooks_input_query_too_short():
    """SearchRunbooksInput should reject query < 3 characters."""
    with pytest.raises(ValidationError) as exc_info:
        SearchRunbooksInput(query="ab", max_results=5)
    assert "at least 3 characters" in str(exc_info.value).lower()


def test_search_runbooks_input_query_too_long():
    """SearchRunbooksInput should reject query > 100 characters."""
    long_query = "a" * 101
    with pytest.raises(ValidationError) as exc_info:
        SearchRunbooksInput(query=long_query, max_results=5)
    assert "at most 100 characters" in str(exc_info.value).lower()


def test_search_runbooks_input_max_results_below_min():
    """SearchRunbooksInput should reject max_results < 1."""
    with pytest.raises(ValidationError) as exc_info:
        SearchRunbooksInput(query="valid query", max_results=0)
    assert "greater than or equal to 1" in str(exc_info.value).lower()


def test_search_runbooks_input_max_results_above_max():
    """SearchRunbooksInput should reject max_results > 20."""
    with pytest.raises(ValidationError) as exc_info:
        SearchRunbooksInput(query="valid query", max_results=21)
    assert "less than or equal to 20" in str(exc_info.value).lower()


def test_search_runbooks_input_default_max_results():
    """SearchRunbooksInput should default max_results to 5."""
    validated = SearchRunbooksInput(query="timeout")
    assert validated.max_results == 5


# ─────────────────────────────────────────────
# Test 2: search_runbooks Error Handling
# ─────────────────────────────────────────────

def test_search_runbooks_invalid_query_too_short():
    """search_runbooks should return error for query < 3 chars."""
    result = search_runbooks(query="ab", max_results=5)
    assert "❌" in result
    assert "Invalid arguments" in result


def test_search_runbooks_invalid_max_results():
    """search_runbooks should return error for invalid max_results."""
    result = search_runbooks(query="valid query", max_results=0)
    assert "❌" in result
    assert "Invalid arguments" in result


def test_search_runbooks_invalid_max_results_too_high():
    """search_runbooks should return error for max_results > 20."""
    result = search_runbooks(query="valid query", max_results=21)
    assert "❌" in result
    assert "Invalid arguments" in result


# ─────────────────────────────────────────────
# Test 3: search_runbooks with Mocked ChromaDB
# ─────────────────────────────────────────────

@patch("tools.db_search")
@patch("tools._get_collection")
def test_search_runbooks_no_results(mock_get_collection, mock_db_search):
    """search_runbooks should return ❌ when no matches found."""
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection
    mock_db_search.return_value = []
    
    result = search_runbooks(query="nonexistent incident", max_results=5)
    
    assert "❌ No matching runbooks found" in result
    assert "nonexistent incident" in result


@patch("tools.db_search")
@patch("tools._get_collection")
def test_search_runbooks_single_result(mock_get_collection, mock_db_search):
    """search_runbooks should format single result correctly."""
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection
    mock_db_search.return_value = [
        {
            "id": "INCIDENT-001",
            "title": "Database Timeout",
            "severity": "high",
            "distance": 0.2,
            "document_preview": "Connection pool exhausted during peak load..."
        }
    ]
    
    result = search_runbooks(query="database timeout", max_results=5)
    
    assert "✅ Found 1 matching runbooks" in result
    assert "INCIDENT-001" in result
    assert "Database Timeout" in result
    assert "high" in result
    assert "0.80" in result  # 1 - 0.2 = 0.80


@patch("tools.db_search")
@patch("tools._get_collection")
def test_search_runbooks_multiple_results(mock_get_collection, mock_db_search):
    """search_runbooks should format multiple results correctly."""
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection
    mock_db_search.return_value = [
        {
            "id": "INCIDENT-001",
            "title": "Database Timeout",
            "severity": "high",
            "distance": 0.15,
            "document_preview": "Connection pool exhausted..."
        },
        {
            "id": "INCIDENT-002",
            "title": "Memory Leak",
            "severity": "medium",
            "distance": 0.35,
            "document_preview": "Memory usage gradually increases..."
        }
    ]
    
    result = search_runbooks(query="timeout leak", max_results=5)
    
    assert "✅ Found 2 matching runbooks" in result
    assert "INCIDENT-001" in result
    assert "INCIDENT-002" in result
    assert "Database Timeout" in result
    assert "Memory Leak" in result
    # Match scores should be 1 - distance
    assert "0.85" in result  # 1 - 0.15
    assert "0.65" in result  # 1 - 0.35


@patch("tools.db_search")
@patch("tools._get_collection")
def test_search_runbooks_respects_max_results(mock_get_collection, mock_db_search):
    """search_runbooks should pass max_results to db_search."""
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection
    mock_db_search.return_value = []
    
    search_runbooks(query="test query", max_results=10)
    
    # Verify db_search was called with correct max_results
    mock_db_search.assert_called_once()
    call_kwargs = mock_db_search.call_args[1]
    assert call_kwargs["n_results"] == 10


# ─────────────────────────────────────────────
# Test 4: Integration Test (Real ChromaDB)
# ─────────────────────────────────────────────

def test_search_runbooks_integration_with_real_db():
    """Integration test: search_runbooks with real seeded database."""
    # This test uses a real ChromaDB instance (seeded from src/data/)
    # It's an integration test, so we allow it to be slower
    
    result = search_runbooks(query="database timeout connection", max_results=3)
    
    # Should find results (assuming data files exist)
    # If no data files, should return "No matching runbooks" gracefully
    if "❌ No matching runbooks" not in result:
        # We found matches — verify structure
        assert "✅ Found" in result
        assert "INCIDENT-" in result  # Should have runbook IDs
        assert "Severity:" in result
        assert "Match score:" in result


def test_search_runbooks_integration_boundary_values():
    """Integration test: search_runbooks with boundary input values."""
    # min valid query: exactly 3 chars
    result_min = search_runbooks(query="cpu", max_results=1)
    assert "❌ Invalid" not in result_min
    
    # max valid query: 100 chars
    long_query = "a" * 100
    result_max = search_runbooks(query=long_query, max_results=20)
    assert "❌ Invalid" not in result_max
    
    # Both should not crash
    assert isinstance(result_min, str)
    assert isinstance(result_max, str)


if __name__ == "__main__":
    print("Running Phase 3 Tool Tests...")
    print("=" * 70)
    
    # Run pytest programmatically
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v"],
        cwd=Path(__file__).parent.parent
    )
    
    exit(result.returncode)
