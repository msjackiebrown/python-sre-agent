# Architecture Pattern — Layered Separation of Concerns

## Why This Pattern?

When building any application with data storage, separate concerns into **3 layers**:

```
Layer 1: Data Access      ← "What can I do with the store?"
    CRUD (Create/Read/Update/Delete) operations
    No knowledge of files, users, or business rules
    Example: add(), remove(), update(), search()

Layer 2: Business Logic   ← "How do I use the store?"
    Orchestrates data access + validation
    Knows about file formats, business rules, domain logic
    Example: seed_runbooks(), validate_input(), process_query()

Layer 3: Presentation     ← "What does the user see?"
    CLI, UI, API — just takes input and displays output
    Calls business logic, never talks to data access directly
    Example: main.py CLI, Streamlit UI, FastAPI endpoints
```

## The Golden Rule

> **Each layer only talks to the layer below it. Never skip layers.**

```
Layer 3 (CLI)         → calls Layer 2 (Business)   ✓ OK
Layer 2 (Business)    → calls Layer 1 (Data Access) ✓ OK  
Layer 3 (CLI)         → calls Layer 1 (Data Access) ✗ WRONG
Layer 1 (Data Access) → calls Layer 2 (Business)    ✗ WRONG
```

## What Each Layer Contains

### Layer 1: Data Access (`data_access.py`)

**Contains:**
- Functions that directly interact with storage technology
- Pure CRUD operations
- No file I/O, no user input handling, no business rules

**Functions:**
```python
def add_runbook(collection, id, document, metadata) -> bool
def remove_runbook(collection, runbook_id) -> bool
def search_runbooks(collection, query, n_results=3) -> list
def init_collection(name, space="cosine") -> tuple
```

**Not Contains:**
- Reading .md files from disk ❌
- Parsing YAML frontmatter ❌
- Validating user input ❌
- Any ChromaDB-specific setup beyond basic operations ❌

### Layer 2: Business Logic (`db.py` or `business/`)

**Contains:**
- Orchestration of data access calls
- Validation logic (what makes a "valid" runbook?)
- Parsing (YAML frontmatter, file formats)
- Domain-specific rules ("must have id, title, severity fields")

**Functions:**
```python
def parse_frontmatter(content: str) -> dict  # Parse YAML from markdown
def seed_runbooks(data_dir) -> int            # Load files → validate → store
def load_from_file(filepath) -> tuple | None  # Parse single runbook
```

**Not Contains:**
- Printing to console ❌
- Taking user input ❌
- HTTP request handling ❌
- Direct storage technology calls ❌

### Layer 3: Presentation (`main.py` or `presentation/`)

**Contains:**
- User interface (CLI, UI buttons, API routes)
- Input/output formatting
- Orchestration of the overall flow

**Code:**
```python
# CLI example
query = input("Enter query: ")  # Take user input
results = search(query)          # Call business logic
print(results)                   # Format and display output
```

## Example Flow — Search Runbook

```
User types: "database timeout"
                    ↓
       main.py (Layer 3)
       ├─ Takes input from user
       └─ Calls search_runbooks()
                    ↓
       db.py (Layer 2)
       ├─ Validates query (min 3 chars, max 100)
       └─ Calls collection.query()
                    ↓
       data_access.py (Layer 1)
       └─ ChromaDB.search(query="database timeout")
                    ↓
       Returns list of matching runbooks
                    ↓
       db.py validates results
       Returns to main.py
                    ↓
       main.py formats and prints results
```

## When to Create a New Layer?

**Create a new layer when:**
1. One layer starts doing jobs from another layer (e.g., CLI reading .md files)
2. You want to reuse logic in multiple contexts (CLI + API share same search)
3. Testing becomes hard because functions have too many responsibilities

**Do NOT create a new layer when:**
1. It's just one simple function (don't over-engineer!)
2. The app is small enough that layers add noise, not value

## Testing Strategy Per Layer

| Layer | Test Type | How |
|-------|-----------|-----|
| Data Access | Unit tests | Mock the storage, test each CRUD function |
| Business Logic | Integration tests | Use real data access, test orchestration |
| Presentation | Manual/CLI testing | Just run it and verify output looks right |

## Anti-Patterns to Avoid

### ❌ Bad: Blended Layers
```python
def main():  # This file does EVERYTHING — bad!
    with open("data/runbook.md") as f:          # Business (file I/O)
        content = f.read()
    metadata = yaml.safe_load(content)            # Business (parsing)
    
    client = chromadb.Client()                    # Data Access
    collection = client.get_or_create_collection()  # Data Access
    
    results = collection.query(...)                # Data Access
    
    for r in results:                              # Presentation
        print(r["title"])
```

### ✅ Good: Separated Layers
```python
# main.py (Presentation)
results = search_runbooks("database timeout")     # Call business layer
for r in results:
    print(r["title"])                               # Format output

# db.py (Business Logic)
def search_runbooks(query):                         # Validate, parse, orchestrate
    validate_query(query)                            # Business rule
    return data_access.search_runbooks(collection, query)  # Delegate to data layer

# data_access.py (Data Access)
def search_runbooks(collection, query):             # Pure storage operation
    return collection.query(...)                    # Nothing but storage
```
