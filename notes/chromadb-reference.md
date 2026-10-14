---
title: ChromaDB Reference Guide - Vector Search for Runbooks
subject: ChromaDB Setup & Usage for SRE Agent
date: 2026-10-14
tags: [chromadb, vector-database, embeddings, semantic-search, rag]
source: https://www.trychroma.com/docs
---

## 🚀 **What is ChromaDB?**

ChromaDB is a **vector database** — it stores data as embeddings (numerical vectors) and finds similar data by comparing vectors.

**Why for your SRE agent?**
- User queries runbooks: *"Database is timing out"*
- ChromaDB converts this to a vector and finds similar runbooks
- Returns relevant `INCIDENT-001.md` (Database Connection Timeout)
- No keyword matching needed — semantic similarity works

**For your project:**
- Store: 7 mock runbooks (INCIDENT-001 through INCIDENT-007)
- Query: User's incident description
- Return: Top 5 matching runbooks with steps + contact info

---

## 📦 **Installation**

```bash
pip install chromadb
```

That's it! No server to run, no configuration needed.

---

## 🏗️ **Core Concepts**

### In-Memory vs Persistent

| Mode | Use Case | Data Survival |
|------|----------|---------------|
| **In-Memory** | Development, demos, ephemeral data | Lost on restart |
| **Persistent** | Production, permanent storage | Survives restarts |

**For your project:** In-Memory (portfolio demo, no persistence needed)

---

## 💾 **Setup: In-Memory (Recommended for You)**

```python
import chromadb

# Create in-memory client (no files, no server)
client = chromadb.Client()

# Get or create a collection
collection = client.get_or_create_collection(
    name="runbooks",
    metadata={"hnsw:space": "cosine"}  # Use cosine similarity
)

print(f"Collection: {collection.name}")
print(f"Count: {collection.count()}")  # 0 initially
```

**What happens:**
- Everything in RAM (fast, temporary)
- Ideal for recruiter demos (no setup friction)
- Perfect for Phase 2 prototyping

---

## 📝 **Adding Documents (Seeding Runbooks)**

### Option 1: Add One Document at a Time

```python
collection.add(
    ids=["incident-001"],  # Unique ID
    documents=["Database connection pool exhausted. Connections refused. Max connections reached."],
    metadatas=[{"title": "Database Connection Timeout", "severity": "high"}]
)
```

### Option 2: Bulk Add (Better for Startup)

```python
# Prepare runbook data
runbooks = [
    {
        "id": "incident-001",
        "title": "Database Connection Timeout",
        "keywords": "timeout database connection pool peak load latency",
        "steps": "1. Check pool status\n2. Increase max_connections\n3. Review slow query log\n4. Restart replication slave",
        "contact": "db-oncall@team.slack.com",
        "escalate": "Platform team lead after 15min"
    },
    {
        "id": "incident-002",
        "title": "Service 5xx Errors",
        "keywords": "error 500 502 503 service down unavailable",
        "steps": "1. GET /health\n2. Review panic logs\n3. Verify dependencies\n4. Graceful restart\n5. Monitor recovery",
        "contact": "platform-oncall@team.slack.com",
        "escalate": "SRE manager after 5min"
    }
]

# Bulk add to collection
collection.add(
    ids=[r["id"] for r in runbooks],
    documents=[r["keywords"] for r in runbooks],  # Search on keywords
    metadatas=[{
        "title": r["title"],
        "steps": r["steps"],
        "contact": r["contact"],
        "escalate": r["escalate"]
    } for r in runbooks]
)
```

**Key insight:** Store keywords in `documents` (for semantic search), full details in `metadatas` (returned with results)

---

## 🔍 **Querying (Searching for Runbooks)**

### Simple Query

```python
results = collection.query(
    query_texts=["database timeout"],  # User's search term
    n_results=5                         # Return top 5 matches
)

print(results)
# Output structure:
# {
#     'ids': [['incident-001']],
#     'distances': [[0.15]],  # Lower = better match (cosine distance)
#     'metadatas': [[{'title': '...', 'steps': '...', 'contact': '...'}]],
#     'documents': [['timeout database connection pool...']]
# }
```

### Processing Query Results

```python
def search_runbooks(query: str, max_results: int = 5) -> str:
    """Search and format runbook results."""
    
    results = collection.query(
        query_texts=[query],
        n_results=max_results
    )
    
    # Check if results found
    if not results['documents'] or not results['documents'][0]:
        return f"❌ No matching runbook found for: '{query}'"
    
    # Format results for LLM
    formatted = []
    for i, (doc_id, metadata) in enumerate(
        zip(results['ids'][0], results['metadatas'][0])
    ):
        formatted.append(
            f"📋 {i+1}. {metadata['title']}\n"
            f"   Steps: {metadata['steps']}\n"
            f"   Contact: {metadata['contact']}\n"
            f"   Escalate: {metadata['escalate']}"
        )
    
    return "\n\n".join(formatted)

# Test it
result = search_runbooks("database timeout")
print(result)
```

---

## 🎯 **Full Startup Pattern (For Your Agent)**

```python
import chromadb
from pathlib import Path
import json

class RunbookDatabase:
    """Manages ChromaDB collection of runbooks."""
    
    def __init__(self):
        """Initialize in-memory ChromaDB and seed runbooks."""
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name="runbooks",
            metadata={"hnsw:space": "cosine"}
        )
        self._seed_runbooks()
    
    def _seed_runbooks(self):
        """Load all INCIDENT-*.md files at startup."""
        runbook_dir = Path("src/data")
        
        runbooks = []
        for incident_file in sorted(runbook_dir.glob("INCIDENT-*.md")):
            # Parse runbook (simplified)
            with open(incident_file) as f:
                content = f.read()
            
            # Extract key fields (you'll refine this)
            runbooks.append({
                "id": incident_file.stem,  # "INCIDENT-001"
                "title": content.split("\n")[0].strip("# "),
                "keywords": content,  # Full content for semantic search
                "steps": content,     # Return full content to LLM
            })
        
        if runbooks:
            self.collection.add(
                ids=[r["id"] for r in runbooks],
                documents=[r["keywords"] for r in runbooks],
                metadatas=[{
                    "title": r["title"],
                    "content": r["steps"]
                } for r in runbooks]
            )
            print(f"✅ Seeded {len(runbooks)} runbooks")
        else:
            print("⚠️ No runbooks found in src/data/")
    
    def search(self, query: str, max_results: int = 5) -> str:
        """Search runbooks by keyword."""
        try:
            if not query or len(query) < 3:
                return "❌ Query must be at least 3 characters"
            
            results = self.collection.query(
                query_texts=[query],
                n_results=max_results
            )
            
            if not results['documents'][0]:
                return f"❌ No matching runbook found for: '{query}'"
            
            formatted = []
            for title, content in zip(
                [m['title'] for m in results['metadatas'][0]],
                [m['content'] for m in results['metadatas'][0]]
            ):
                formatted.append(f"📋 **{title}**\n```\n{content}\n```")
            
            return "\n\n".join(formatted)
        
        except Exception as e:
            return f"⚠️ Search error: {str(e)}"


# Usage
if __name__ == "__main__":
    db = RunbookDatabase()
    
    # Test searches
    print(db.search("database timeout"))
    print(db.search("memory leak"))
```

---

## 📊 **Distance Metrics (What Lower Distances Mean)**

ChromaDB supports different distance metrics:

| Metric | Range | Better Match |
|--------|-------|--------------|
| **cosine** (default) | 0-2 | 0 (identical) |
| **euclidean** | 0-∞ | 0 (identical) |
| **manhattan** | 0-∞ | 0 (identical) |

**For your use case:** Use `cosine` (default) — best for text similarity.

---

## 🔧 **Common Operations**

### Count Documents in Collection

```python
count = collection.count()
print(f"Total runbooks: {count}")
```

### Get All Documents

```python
all_docs = collection.get()
print(f"IDs: {all_docs['ids']}")
print(f"Count: {len(all_docs['ids'])}")
```

### Delete a Document

```python
collection.delete(ids=["incident-001"])
```

### Clear Entire Collection

```python
collection.delete_where()  # Deletes all
```

### Get by ID

```python
doc = collection.get(ids=["incident-001"])
print(doc['metadatas'][0])
```

---

## ⚡ **Performance Tips**

1. **Batch operations** — Add many docs at once instead of one-by-one
2. **Indexed columns** — Use `delete_where()` efficiently with metadata filters
3. **In-memory** — Faster than persistent for demos
4. **Pre-compute embeddings** — ChromaDB does this automatically

---

## 🧪 **Quick Test: Verify Your Setup**

```python
import chromadb

# Create client
client = chromadb.Client()
collection = client.get_or_create_collection("test")

# Add sample data
collection.add(
    ids=["test-1", "test-2"],
    documents=[
        "The database connection timed out due to high load",
        "Memory usage spiked to 90% capacity"
    ]
)

# Query
results = collection.query(
    query_texts=["why is database slow"],
    n_results=2
)

print("✅ ChromaDB working!" if results['documents'][0] else "❌ Failed")
```

---

## 🎯 **For Your SRE Agent**

### Minimal Integration

```python
# src/runbook_db.py
import chromadb

class RunbookSearch:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("runbooks")
        # Seed runbooks here
    
    def search(self, query: str) -> str:
        results = self.collection.query(query_texts=[query], n_results=5)
        # Format and return to LLM

# src/agent.py
from runbook_db import RunbookSearch

db = RunbookSearch()
result = db.search("database timeout")
```

---

## 📚 **Resources**

- **Official Docs:** https://www.trychroma.com/docs
- **API Reference:** https://docs.trychroma.com/api-reference
- **GitHub:** https://github.com/chroma-core/chroma
- **Embeddings Guide:** https://www.trychroma.com/docs/embeddings/overview

---

## ✅ **Checklist for Phase 3**

- [ ] Install ChromaDB: `pip install chromadb`
- [ ] Create `src/runbook_db.py` with `RunbookDatabase` class
- [ ] Seed 7 runbooks (INCIDENT-001 through INCIDENT-007) at startup
- [ ] Implement `search_runbooks()` to query collection
- [ ] Test: `search_runbooks("database timeout")` returns INCIDENT-001
- [ ] Test: `search_runbooks("hello world")` returns "No matching runbook"
- [ ] Integrate into agent loop's tool calling

---

## 🚀 **Next: Implementation**

Ready to implement ChromaDB integration in your agent? Here's the workflow:

1. Create `src/runbook_db.py` with `RunbookDatabase` class
2. Modify `src/agent.py` to initialize DB on startup
3. Update `src/tools.py` `search_runbooks()` to use DB queries
4. Test with sample queries
5. Verify with Qwen 2.5-7B

You've got this! 💪
