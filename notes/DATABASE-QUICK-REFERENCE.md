# 🎯 Database Layer — Quick Reference Card

## The Pattern You'll Reuse in Every Project

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: PRESENTATION (main.py)                                 │
│ User Input/Output — "What does the user see?"                   │
│ ❌ NO database calls here                                        │
│ ✅ Takes input → calls tools → prints results                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓ calls
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: BUSINESS LOGIC (tools.py)                              │
│ Orchestration & Validation — "How do we use the database?"      │
│ ❌ NO file I/O, NO UI code here                                 │
│ ✅ Parse files, validate input, call Layer 1                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓ calls
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: DATA ACCESS (db.py)                                    │
│ Pure CRUD — "What can I do with the storage?"                   │
│ ❌ NO parsing, NO validation, NO UI                             │
│ ✅ add() search() remove() update() count()                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓ interacts
┌─────────────────────────────────────────────────────────────────┐
│ ChromaDB (Vector Store)                                         │
│ Stores documents + metadata, performs semantic search           │
└─────────────────────────────────────────────────────────────────┘
```

## The Golden Rule

> **Each layer ONLY talks to the layer BELOW it. Never skip layers.**

```
✓ CORRECT                      ✗ WRONG
main → tools → db             main → db (skip tools)
tools → db                    db → tools (reversed)
```

## Data Format at a Glance

### File: `src/data/INCIDENT-001.md`

```markdown
---
id: INCIDENT-001                    ← Unique identifier
title: Database Timeout             ← Human-readable name
severity: high                      ← critical/high/medium
keywords: database timeout slow     ← Search hints
contact: db-oncall@company.com      ← Who to page
---

## Overview
Our database connection pool exhausts during peak traffic...

## Root Cause
...
```

## API (Layer 1: db.py) — Copy This Pattern

```python
from db import init_collection, add_runbook, search_runbooks, remove_runbook

# Get connection
client, collection = init_collection("my_runbooks")

# Store a runbook
add_runbook(collection, "INC-001", full_markdown_text, metadata_dict)

# Search
results = search_runbooks(collection, "database timeout", n_results=3)
# Returns: [{"id": "INC-001", "title": "...", "severity": "high", ...}, ...]

# Delete
remove_runbook(collection, "INC-001")
```

## Testing at a Glance

```bash
python -m pytest tests/test_db.py -v

# Tests coverage:
test_parse_frontmatter_returns_dict        ✅
test_parse_frontmatter_missing_frontmatter ✅
test_parse_frontmatter_empty_frontmatter   ✅
test_seed_runbooks_counts_correctly        ✅
test_seed_runbooks_stores_metadata         ✅
test_seed_runbooks_only_loads_md_files     ✅
test_parse_frontmatter_with_multiline_values ✅
test_parse_frontmatter_numeric_values      ✅

======================== 8 passed ========================
```

## Why This Pattern Works

| Problem | Solution | Benefit |
|---------|----------|---------|
| Files do too many things | Separate into 3 layers | Easy to understand, easy to test |
| Hard to swap databases | DB logic only in Layer 1 | Change ChromaDB → Weaviate in 1 file |
| Tests are slow/flaky | Test layers independently | Fast unit tests, no I/O, no flakiness |
| Hard to reuse code | Each layer is independent | CLI uses same tools as API server |

## When You Need to Change Something

### "I need to change how we search"
Edit: `src/db.py` → `search_runbooks()` function

### "I need to add validation (min query length)"
Edit: `src/tools.py` → `search_runbooks()` function

### "I need to change the display format"
Edit: `src/main.py` → `main()` function

### "I need to change from ChromaDB to Weaviate"
Edit: `src/db.py` → `init_collection()` + `search_runbooks()`  
Everything else stays the same ✅

## Files to Reference

| When You Need | Read This |
|---------------|-----------|
| **Full database explanation** | `notes/DATABASE-MASTER-GUIDE.md` |
| **Layer 1 (db.py) details** | `notes/db-layer-explanation.md` |
| **Three-layer pattern** | `notes/layered-architecture-pattern.md` |
| **What's done, what's next** | `notes/DATABASE-COMPLETION-CHECKLIST.md` |
| **Complete code** | `src/db.py`, `src/tools.py`, `src/main.py` |
| **Complete tests** | `tests/test_db.py` |

## Quick Copy-Paste for Future Projects

When starting a new project (blog, e-commerce, etc.):

1. Copy this structure:
   ```
   src/
     db.py       ← Pure CRUD operations
     tools.py    ← Business logic + file I/O
     main.py     ← User interface
   tests/
     test_db.py  ← Unit tests for each layer
   ```

2. Replace ChromaDB with your database (SQL, Mongo, etc.)

3. Copy the three-layer pattern

4. Update docstrings for your domain

That's it. You've just saved hours of architecture design.

## The Principle You're Learning

```
Every application with data storage has three concerns:
1. How do I store/retrieve data? (Layer 1)
2. How do I process/validate data? (Layer 2)  
3. How do I show it to the user? (Layer 3)

When you confuse these, your code becomes spaghetti.
When you separate them, your code becomes modular.
```

---

**Print this card. Tape it to your monitor. Use it in every project.**
