"""Tests for src/db.py — runbook loading into ChromaDB."""
import os
import tempfile
from pathlib import Path

# Import the functions we test (without running top-level seed)
from db import parse_frontmatter, seed_runbooks


# ─────────────────────────────────────────────
# Test 1: parse_frontmatter extracts YAML correctly
# ─────────────────────────────────────────────
def test_parse_frontmatter_returns_dict():
    """parse_frontmatter should return a dict from valid YAML."""
    markdown = """---
id: INCIDENT-001
title: Database Timeout
severity: high
---
Some body text after frontmatter."""

    result = parse_frontmatter(markdown)
    
    assert isinstance(result, dict), "Should return a dictionary"
    assert result["id"] == "INCIDENT-001"
    assert result["title"] == "Database Timeout"
    assert result["severity"] == "high"


def test_parse_frontmatter_missing_frontmatter():
    """parse_frontmatter should return empty dict when no YAML frontmatter."""
    markdown = "No frontmatter here, just plain text."
    
    result = parse_frontmatter(markdown)
    
    assert result == {}, "Should return empty dict when no frontmatter"


def test_parse_frontmatter_empty_frontmatter():
    """parse_frontmatter should handle empty YAML block gracefully."""
    markdown = """---
---
Some content after empty frontmatter."""

    result = parse_frontmatter(markdown)
    
    assert result == {}, "Should return empty dict for empty YAML"


# ─────────────────────────────────────────────
# Test 2: seed_runbooks loads runbooks into ChromaDB
# ─────────────────────────────────────────────
def test_seed_runbooks_counts_correctly():
    """seed_runbooks should load all .md files and return correct count."""
    # Create a temporary directory with test markdown files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write 3 test runbooks
        for i in range(1, 4):
            md_content = f"""---
id: INCIDENT-{i:03d}
title: Test Incident {i}
severity: medium
---
Body of incident {i}."""
            filepath = os.path.join(tmpdir, f"INCIDENT-{i:03d}.md")
            with open(filepath, "w") as f:
                f.write(md_content)
        
        # Call seed function (not the module-level script)
        collection, count = seed_runbooks(data_dir=tmpdir)
    
    assert count == 3, f"Expected 3 runbooks seeded, got {count}"


def test_seed_runbooks_stores_metadata():
    """seed_runbooks should store metadata correctly in ChromaDB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        md_content = """---
id: INCIDENT-999
title: Test Metadata Incident
severity: critical
---
Test body."""
        filepath = os.path.join(tmpdir, "INCIDENT-999.md")
        with open(filepath, "w") as f:
            f.write(md_content)
        
        collection, count = seed_runbooks(data_dir=tmpdir)
    
    # Query the stored data to verify metadata was saved correctly
    results = collection.get(ids=["INCIDENT-999"])
    
    assert len(results["metadatas"]) == 1
    meta = results["metadatas"][0]
    assert meta["id"] == "INCIDENT-999"
    assert meta["title"] == "Test Metadata Incident"
    assert meta["severity"] == "critical"


def test_seed_runbooks_only_loads_md_files():
    """seed_runbooks should ignore non-.md files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write a .md file (should be loaded)
        md_content = "---\nid: INCIDENT-100\ntitle: Test\nseverity: medium\n---\nBody."
        with open(os.path.join(tmpdir, "INCIDENT-100.md"), "w") as f:
            f.write(md_content)
        
        # Write a .txt file (should be ignored)
        with open(os.path.join(tmpdir, "notes.txt"), "w") as f:
            f.write("This should not be loaded.")
        
        # Write a .json file (should be ignored)
        with open(os.path.join(tmpdir, "data.json"), "w") as f:
            f.write('{"not": "loaded"}')
        
        collection, count = seed_runbooks(data_dir=tmpdir, collection_name="test_md_filter")
    
    assert count == 1, f"Should only load .md files, got {count}"


# ─────────────────────────────────────────────
# Test 3: parse_frontmatter handles edge cases
# ─────────────────────────────────────────────
def test_parse_frontmatter_with_multiline_values():
    """parse_frontmatter should handle multi-line values correctly."""
    # In YAML, multiline string values must be quoted
    markdown = """---
title: "A very long title that spans multiple lines"
keywords: "foo, bar, baz"
---
Body."""

    result = parse_frontmatter(markdown)
    
    assert "title" in result
    assert "foo, bar, baz" in result["keywords"]


def test_parse_frontmatter_numeric_values():
    """parse_frontmatter should convert numeric YAML values to integers/floats."""
    markdown = "---\nseverity: 1\npriority: 0.5\ncount: 42\n---\nBody."

    result = parse_frontmatter(markdown)
    
    assert isinstance(result["severity"], int), "severity should be int"
    assert isinstance(result["priority"], float), "priority should be float"
    assert result["count"] == 42


if __name__ == "__main__":
    print("Running tests...")
    test_parse_frontmatter_returns_dict()
    print("✅ parse_frontmatter returns dict correctly")
    
    test_parse_frontmatter_missing_frontmatter()
    print("✅ parse_frontmatter handles missing frontmatter")
    
    test_seed_runbooks_counts_correctly()
    print("✅ seed_runbooks counts correctly")
    
    test_seed_runbooks_stores_metadata()
    print("✅ seed_runbooks stores metadata correctly")
    
    test_seed_runbooks_only_loads_md_files()
    print("✅ seed_runbooks only loads .md files")
    
    print("\n✅ All tests passed!")
