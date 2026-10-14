# 📚 Master Database Design Guide

**Purpose:** Centralized reference for understanding how the Database Layer (Layer 1) works in this project.

This note consolidates all database-related documentation, design patterns, and testing strategy.

---

## 🎯 Quick Reference

| What | Where | Why |
|------|-------|-----|
| **Data Format** | Markdown files with YAML frontmatter in `src/data/` | Human-readable, version-control friendly, easy to parse |
| **Storage** | ChromaDB (in-memory, ephemeral) | Fast semantic search, no server setup needed, local-only |
| **Separation** | Layer 1 (db.py), Layer 2 (tools.py), Layer 3 (main.py) | Each layer has one job, easy to test and maintain |
| **Tests** | `tests/test_db.py` (8 test cases) | Verify parsing, seeding, edge cases independently |
| **API** | `db.init_collection()`, `db.add_runbook()`, `db.search_runbooks()` | Pure CRUD operations, no business logic |

---

## 🏗️ The Three Layers (Layered Architecture Pattern)

```
┌──────────────────────────────────────────────────────┐
│ Layer 3: PRESENTATION                                │
│ main.py — User Input/Output                          │
│ └─ Takes query from console                          │
│    Prints formatted results                          │
└──────────────────────────────────────────────────────┘
                        ↓ calls
┌──────────────────────────────────────────────────────┐
│ Layer 2: BUSINESS LOGIC                              │
│ tools.py — Orchestration & Validation                │
│ └─ Parses YAML frontmatter                           │
│    Validates input ("min 3 chars")                   │
│    Orchestrates seed/search workflows                │
└──────────────────────────────────────────────────────┘
                        ↓ calls
┌──────────────────────────────────────────────────────┐
│ Layer 1: DATA ACCESS                                 │
│ db.py — Pure CRUD Operations                         │
│ └─ init_collection()                                 │
│    add_runbook() / search_runbooks() / remove()      │
│    NO file I/O, NO parsing, NO business rules        │
└──────────────────────────────────────────────────────┘
                        ↓ interacts
┌──────────────────────────────────────────────────────┐
│ ChromaDB (Vector Store)                              │
│ └─ Stores documents (full runbook text)              │
│    Stores metadata (id, title, severity, keywords)   │
│    Performs semantic similarity search               │
└──────────────────────────────────────────────────────┘
```

### The Golden Rule

> **Each layer only talks to the layer BELOW it. Never skip layers.**

```
✓ CORRECT                          ✗ WRONG
main.py → tools.py → db.py        main.py → db.py (skip tools)
tools.py → db.py                  db.py → tools.py (reversed)
```

---

## 📋 Data Format: Runbook Markdown Files

### File Structure

Each runbook is a single `.md` file with **YAML frontmatter** at the top:

```markdown
---
id: INCIDENT-001
title: Database Connection Timeout During Peak Load
severity: high
keywords: database connection timeout slow performance
contact: db-oncall@company.com
---

## Overview
Our database connection pool exhausts during peak traffic (9-11am UTC).

## Root Cause
...

## Steps to Resolve
1. Check active connections: SELECT count(*) FROM pg_stat_activity;
2. If > 80 connections, scale up the pool...
```

### YAML Frontmatter Fields (Required)

| Field | Type | Example | Why |
|-------|------|---------|-----|
| `id` | string | `INCIDENT-001` | Unique identifier for the runbook |
| `title` | string | `Database Connection Timeout...` | Human-readable name for search results |
| `severity` | enum | `critical`, `high`, `medium` | Filter runbooks by urgency |
| `keywords` | string | `database connection timeout slow` | Semantic search hints |
| `contact` | string | `db-oncall@company.com` | On-call team for this runbook |

**Why YAML Frontmatter?**
- Separates metadata (searchable fields) from runbook body (long documentation)
- Standard in static site generators (Hugo, Jekyll), familiar pattern
- Easy to parse with `yaml.safe_load()` — no custom parser needed
- Human-readable format — can edit directly in VS Code

---

## 💾 Storage: ChromaDB (Vector Store)

### Why ChromaDB?

| Feature | Why Matters |
|---------|------------|
| **In-Memory** | No database server needed — zero infrastructure |
| **Ephemeral** | Fresh on each run — no stale cached data |
| **Semantic Search** | Searches by *meaning*, not keywords → "database timeout" finds "connection pool exhaustion" |
| **Local-Only** | All data stays on your machine (privacy/compliance friendly) |
| **Simple API** | `collection.add()`, `collection.query()`, `collection.delete()` |

### How ChromaDB Stores Data

When you call `db.add_runbook(collection, "INC-001", document_text, metadata)`:

```python
# What's stored:
{
  "id": "INC-001",                          # Unique key
  "document": "---\nid: INCIDENT-001\n...",  # Full text (embedded + searchable)
  "metadata": {                             # Metadata fields (filtered, not embedded)
    "id": "INCIDENT-001",
    "title": "Database Timeout",
    "severity": "high",
    "keywords": "database connection timeout",
    "contact": "db-oncall@company.com"
  }
}
```

**Document:** Full runbook markdown (gets embedded into vector space for semantic search).

**Metadata:** YAML fields stored as-is (not embedded, only used for filtering/display).

### How Search Works

User queries: `"database is slow"`

```
Query → ChromaDB Embedding → Vector Space → Find similar documents → Return with distances
```

Result:
```python
[
  {
    "id": "INCIDENT-001",
    "title": "Database Connection Timeout...",
    "severity": "high",
    "distance": 0.23,  # Lower = more similar
    "document_preview": "---\nid: INCIDENT-001\n...[200 chars]"
  }
]
```

---

## 🧪 Testing Strategy

### Test File: `tests/test_db.py`

8 comprehensive test cases covering:

| Test | What It Proves | Layer |
|------|----------------|-------|
| `test_parse_frontmatter_returns_dict` | YAML → Python dict works | Business Logic (tools.py pattern) |
| `test_parse_frontmatter_missing_frontmatter` | No YAML → returns `{}` safely | Edge case handling |
| `test_parse_frontmatter_empty_frontmatter` | Empty `--- ---` → returns `{}` | Edge case handling |
| `test_seed_runbooks_counts_correctly` | 3 files → count=3 | Data Access (db.py pattern) |
| `test_seed_runbooks_stores_metadata` | Metadata stored correctly | Data persistence |
| `test_seed_runbooks_only_loads_md_files` | Ignores `.txt`, `.json` — only `.md` | File type filtering |
| `test_parse_frontmatter_with_multiline_values` | Quoted strings parse correctly | YAML edge case |
| `test_parse_frontmatter_numeric_values` | `severity: 1` → int type preserved | Type handling |

### Why These Tests?

1. **Test each layer independently:** Tests don't import `main.py` (no user I/O), only test db + tools logic
2. **Test edge cases early:** Catches bugs before they reach users
3. **Document expected behavior:** Tests serve as executable documentation ("this is how YAML parsing should work")
4. **Enable refactoring safely:** If you change the database backend later, tests catch breakage

### Running Tests

```bash
python -m pytest tests/test_db.py -v
```

Expected output:
```
tests/test_db.py::test_parse_frontmatter_returns_dict PASSED
tests/test_db.py::test_parse_frontmatter_missing_frontmatter PASSED
...
======================== 8 passed in 4.10s ========================
```

---

## 🔧 API Reference: db.py (Layer 1)

### `init_collection(collection_name="runbooks", space="cosine")`

Create or get a ChromaDB collection for storing runbooks.

```python
from db import init_collection

client, collection = init_collection("my_runbooks")
# Returns: (ChromaDB client object, collection object)
```

**Why return both?** The collection is what you pass to other functions. Client is kept for advanced operations.

---

### `add_runbook(collection, runbook_id, document, metadata)`

Add a single runbook to the vector store.

```python
from db import add_runbook

success = add_runbook(
    collection,
    runbook_id="INCIDENT-001",
    document="---\nid: INCIDENT-001\n...",  # Full markdown
    metadata={"title": "Database Timeout", "severity": "high", ...}
)
# Returns: True if added, False if duplicate ID exists
```

**When to use:** When ingesting one runbook at a time (e.g., `tools.seed_runbooks()` calls this in a loop).

---

### `search_runbooks(collection, query, n_results=3)`

Search runbooks by semantic similarity.

```python
from db import search_runbooks

results = search_runbooks(collection, "database timeout", n_results=5)
# Returns: List of dicts with id, title, severity, distance, document_preview
```

Example output:
```python
[
  {
    "id": "INCIDENT-001",
    "title": "Database Connection Timeout During Peak Load",
    "severity": "high",
    "distance": 0.23,
    "document_preview": "## Overview\nOur database connection pool..."
  },
  ...
]
```

---

### `remove_runbook(collection, runbook_id)`

Delete a runbook from the collection.

```python
from db import remove_runbook

success = remove_runbook(collection, "INCIDENT-001")
# Returns: True if deleted, False if not found
```

---

### `count_runbooks(collection)`

Get the number of runbooks in the collection.

```python
from db import count_runbooks

total = count_runbooks(collection)
# Returns: integer count
```

---

## 📊 Data Flow: Full Example

### Scenario: User searches for "database is slow"

```
┌─ main.py (Layer 3)
│  query = input("Enter query: ")  # "database is slow"
│  results = search_runbooks(query)
└─ calls →

┌─ tools.py (Layer 2)
│  def search_runbooks(query):
│      if len(query) < 3:           # Business rule: min 3 chars
│          return []
│      client, collection = init_collection()  # Get connection
│      results = db.search_runbooks(collection, query)  # Call Layer 1
│      return results
└─ calls →

┌─ db.py (Layer 1)
│  def search_runbooks(collection, query, n_results=3):
│      results = collection.query(
│          query_texts=[query],
│          n_results=n_results,
│          include=["documents", "metadatas", "distances"]
│      )
│      # Format and return results
│      return matching
└─ interacts with →

┌─ ChromaDB
│  1. Embeds "database is slow" into vector space
│  2. Finds 3 closest documents by distance
│  3. Returns their ids, metadata, distances
└─

Results bubble back up:
[
  {"id": "INC-001", "title": "Database Timeout...", ...},
  {"id": "INC-003", "title": "Slow Query Performance...", ...},
  {"id": "INC-007", "title": "Connection Pool Exhaustion...", ...},
]

main.py formats and prints:
[HIGH] Database Connection Timeout During Peak Load (INCIDENT-001)
[MEDIUM] Slow Query Performance (INCIDENT-003)
[HIGH] Connection Pool Exhaustion (INCIDENT-007)
```

---

## 🔄 When to Swap Database Technologies

The three-layer pattern makes swapping databases easy. If you wanted to use Weaviate, Pinecone, or Milvus instead of ChromaDB:

**You would ONLY change:** `src/db.py`

**You would NOT touch:** `tools.py`, `main.py`, tests — they still call the same functions.

### Example: Swap ChromaDB → Weaviate

Old `db.py`:
```python
import chromadb
def init_collection(name="runbooks"):
    client = chromadb.EphemeralClient()
    return client.get_or_create_collection(name=name)
```

New `db.py`:
```python
import weaviate
def init_collection(name="runbooks"):
    client = weaviate.Client("http://localhost:8080")
    return client.create_class({"class": name})
```

**That's it.** Every other file stays the same. This is the power of layered architecture.

---

## 📝 Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| **Data Format** | ✅ Complete | Markdown + YAML frontmatter in `src/data/` |
| **Storage** | ✅ Complete | ChromaDB ephemeral (in-memory, local-only) |
| **API** | ✅ Complete | 6 pure CRUD functions in `db.py` |
| **Testing** | ✅ Complete | 8 comprehensive tests in `tests/test_db.py` |
| **Documentation** | ✅ Complete | This master note + individual layer notes |
| **Layered Pattern** | ✅ Complete | Layer 1 (db.py), Layer 2 (tools.py), Layer 3 (main.py) |

---

## 📚 Related Notes

- **[db-layer-explanation.md](./db-layer-explanation.md)** — Detailed explanation of Layer 1 (db.py)
- **[layered-architecture-pattern.md](./layered-architecture-pattern.md)** — Complete three-layer pattern guide
- **[tool-calling.md](./tool-calling.md)** — How the agent uses these tools

---

## 🎓 Key Learnings for Future Projects

This database layer demonstrates three reusable patterns:

1. **Layered Architecture:** Always separate data access (Layer 1) from business logic (Layer 2) from presentation (Layer 3)
2. **YAML Frontmatter:** Great for structured metadata in markdown files
3. **Vector Search:** Use semantic search (ChromaDB) instead of keyword search for better relevance

Apply these patterns to your next project: blog, e-commerce, ML pipeline, etc.
