# Design Decisions: Why These Technologies?

Rationale behind each architectural choice, with trade-offs and alternatives.

---

## Model Selection: Qwen 2.5-7B

### Decision: Ship Qwen 2.5-7B (4.7 GB) as the Default Model

**TL;DR:** Recruiters can actually run this on their laptops. We prove competence on constrained hardware.

### The Problem
- **Large models** (27B+): Better reasoning, but require 24GB+ RAM
- **Recruiters:** Likely have 8-16GB laptops
- **Portfolio projects:** Need to be runnable by your audience

### Our Solution
**Qwen 2.5-7B** is the sweet spot:

| Metric | Qwen 2.5-7B | Qwen 3.8-27B | Llama 3.1-8B |
|--------|----------|------------|-----------|
| **Model Size** | 4.7 GB | 18 GB | 8 GB |
| **RAM Required** | 8-10 GB | 24GB+ | 12-16 GB |
| **Tool Calling** | ✅ Strong | ✅ Excellent | ✅ Good |
| **Inference Speed** | 50+ tok/sec | 10-15 tok/sec | 40+ tok/sec |
| **Available on Ollama** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Interview Readiness** | ✅ Runs on recruiter hardware | ✅ You need 24GB | ⚠️ Medium |

### Why This Matters
- Recruiters clone repo → `ollama run qwen2.5:7b` → Works in 10 minutes
- They see: Full agent loop, tool calling, ReAct pattern
- They test it themselves → Credibility boost

### Alternatives Considered

#### Option A: Use GPT-4 via OpenAI API
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(model="gpt-4", ...)
```

**Pros:**
- ✅ Best reasoning available
- ✅ Strongest tool calling

**Cons:**
- ❌ Requires API key (not suitable for portfolio)
- ❌ Costs money per query
- ❌ Doesn't showcase local AI knowledge
- ❌ Recruiters can't easily test

**Decision:** ❌ Rejected. Portfolio projects should be self-contained.

#### Option B: Use a Smaller Model (Mistral 7B)
**Pros:**
- ✅ Same size as Qwen
- ✅ Also runs locally

**Cons:**
- ❌ Weaker tool calling
- ❌ Less reliable for structured output
- ❌ Qwen has better multilingual support

**Decision:** ❌ Rejected. Qwen 2.5 series is better engineered for agents.

#### Option C: Use Ollama's Default (Llama 2 7B)
**Pros:**
- ✅ Popular, well-known
- ✅ Good performance

**Cons:**
- ❌ Slightly larger (8 GB vs 4.7 GB)
- ❌ Weaker tool calling than Qwen

**Decision:** ❌ Rejected. Qwen more reliable for this use case.

### The Dual-Model Strategy (For Advanced Portfolio)

**Optional enhancement** (mentioned in README):
```bash
# Recruiter tests with Qwen 2.5-7B
streamlit run src/main.py

# You record YouTube demo with Qwen 3.8-27B
ollama run qwen3.8:27b
# Visible reasoning in tool calling = wow factor
```

**Why this works:**
- Recruiter: Tests locally, sees working agent
- YouTube: You show advanced reasoning with larger model
- Interview: You explain the trade-off (speed vs. reasoning depth)

---

## Data Storage: ChromaDB (In-Memory, Ephemeral)

### Decision: Ephemeral ChromaDB, Not Persistent

**TL;DR:** Portfolio projects don't need databases. We want zero infrastructure.

### The Problem
- **Persistent databases:** Require DevOps knowledge (Docker, ports, migrations)
- **Vector databases:** Pinecone requires API keys; Weaviate needs infrastructure
- **Portfolio:** Should "just work" locally

### Our Solution
**Ephemeral ChromaDB:**

```python
from chromadb import EphemeralClient

# Created fresh on every run
client = EphemeralClient()
collection = client.get_or_create_collection(name="runbooks")

# 7 sample runbooks loaded from src/data/*.md
seed_runbooks()

# On exit: Collection discarded, no cleanup needed
```

### Why This Matters
| Approach | Time to Run | DevOps Needed | Persistence |
|----------|----------|--------|-------------|
| **Ephemeral ChromaDB** | 5 min | ❌ None | Single session |
| **Docker Postgres** | 15 min | ✅ Docker | Persisted to disk |
| **Pinecone Cloud** | 20 min | ✅ API keys, cloud account | Persisted in cloud |

**For portfolio:** Ephemeral wins. Runs on any laptop.

### Trade-offs

#### ✅ Pros
- Zero external dependencies
- No authentication/API keys
- Fast startup (milliseconds)
- Perfect for testing

#### ❌ Cons
- Data lost on exit
- Single-session only
- Can't handle multiple concurrent users

### Alternatives Considered

#### Option A: Persistent ChromaDB (SQLite Backend)
```python
from chromadb import PersistentClient

client = PersistentClient(path="./data")
```

**Pros:**
- ✅ Survives across sessions
- ✅ Still zero external dependencies

**Cons:**
- ❌ Slower on startup
- ❌ One user can corrupt DB
- ❌ More complex testing

**Decision:** ⚠️ Keep for Phase 5+ (multi-user scenario)

#### Option B: Pinecone (Cloud Vector DB)
```python
from pinecone import Pinecone

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
```

**Pros:**
- ✅ Scales to millions of vectors
- ✅ Multi-user ready
- ✅ Production-grade

**Cons:**
- ❌ Requires API key
- ❌ Cloud dependency (defeats "local-first")
- ❌ Costs money
- ❌ Overcomplicated for portfolio

**Decision:** ❌ Rejected. Production-only, not portfolio.

#### Option C: Weaviate (Self-Hosted)
```python
import weaviate

client = weaviate.connect_to_local()
```

**Pros:**
- ✅ Self-hosted, controllable
- ✅ Production-grade

**Cons:**
- ❌ Requires Docker
- ❌ Complex setup
- ❌ Overkill for 7 runbooks

**Decision:** ❌ Rejected. Too much infrastructure for portfolio.

### Migration Path for Production
When ready to scale:

```python
# Phase 5: Keep same interface, swap backend
# src/db.py unchanged

# Phase 6: Add Weaviate
from weaviate import connect_to_local
client = connect_to_local()

# Phase 7: Move to Pinecone for cloud deployment
from pinecone import Pinecone
pc = Pinecone(api_key=...)
```

---

## UI Framework: Streamlit (Not FastAPI)

### Decision: Streamlit for Portfolio, FastAPI for Production

**TL;DR:** Quick to build, easy to deploy, perfect for demos.

### The Problem
- **Recruiters want to see:** Working demo
- **Recruiters don't want:** Backend setup, API testing
- **You want:** Fast iteration

### Our Solution
**Streamlit for portfolio:**

```bash
streamlit run src/main.py
# Opens browser automatically
# Chat interface works immediately
# Changes reload on save
```

### Why This Matters
| Criterion | Streamlit | FastAPI | CLI |
|-----------|-----------|---------|-----|
| **Setup time** | 1 min | 5 min | N/A |
| **Demo experience** | ⭐⭐⭐ Web UI | ⭐⭐ JSON API | ⭐ Terminal |
| **Interview impressiveness** | ⭐⭐⭐ Modern app | ⭐⭐ Backend API | ⭐ Raw output |
| **Production-ready** | ❌ Single-threaded | ✅ Async, scalable | ❌ Not designed for it |
| **Code complexity** | 🟢 Simple | 🟡 Moderate | 🟢 Simple |

### Trade-offs

#### ✅ Pros
- Fast iteration (save file → changes reload)
- Beautiful UI out of the box
- Session state management built-in
- Zero backend knowledge needed

#### ❌ Cons
- Single-threaded (can't handle concurrent requests)
- Not designed for high-traffic APIs
- Stateless (each browser tab = new session)

### Alternatives Considered

#### Option A: FastAPI
```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/chat")
def chat(query: str):
    return {"response": react_agent(query)}
```

**Pros:**
- ✅ Production-grade async
- ✅ Perfect for APIs
- ✅ Can handle 1000+ concurrent requests

**Cons:**
- ❌ Recruiter has to test with curl/Postman
- ❌ Slower to build UI (need React/Vue)
- ❌ More setup (requirements.txt, port management)

**Decision:** 🔄 Hybrid approach:
- **Portfolio:** Streamlit (what we have now)
- **Phase 5:** Add FastAPI wrapper for production

#### Option B: Flask
```python
from flask import Flask

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    return {"response": react_agent(...)}
```

**Pros:**
- ✅ Simple, minimal boilerplate

**Cons:**
- ❌ Less async capability than FastAPI
- ❌ Still requires frontend UI work

**Decision:** ❌ Rejected. FastAPI better if we need HTTP API.

#### Option C: CLI Only
```bash
python src/agent.py
# Read from stdin, write to stdout
```

**Pros:**
- ✅ Simplest to build
- ✅ Perfect for Unix pipelines

**Cons:**
- ❌ Not impressive in an interview
- ❌ Hard for recruiters to test interactively

**Decision:** ⚠️ Keep as option for debugging, but Streamlit primary.

### Migration Path for Production
```python
# Phase 5: Dual interface
# Keep Streamlit for demos
# Add FastAPI for production traffic

# src/agent.py → shared logic
# src/main.py → Streamlit UI
# src/api.py → FastAPI routes
```

---

## Type Safety: Pydantic

### Decision: Pydantic v2 for All Input Validation

**TL;DR:** Catches bugs early, generates tool schemas automatically.

### The Problem
- LLM can hallucinate bad tool arguments
- Unvalidated input crashes tools
- Manual validation is tedious

### Our Solution
```python
from pydantic import BaseModel, Field

class SearchRunbooksInput(BaseModel):
    query: str = Field(..., min_length=3, max_length=100)
    max_results: int = Field(5, ge=1, le=20)

# This automatically:
# 1. Validates user input
# 2. Generates JSON schema for tool calling
# 3. Provides helpful error messages
```

### Why This Matters
```python
# ❌ Without Pydantic
def search_runbooks(query, max_results=5):
    if not isinstance(query, str):
        raise TypeError("query must be string")
    if len(query) < 3:
        raise ValueError("query too short")
    if max_results > 20:
        raise ValueError("max_results too large")
    # ... 10 more validation lines

# ✅ With Pydantic
class SearchRunbooksInput(BaseModel):
    query: str = Field(..., min_length=3, max_length=100)
    max_results: int = Field(5, ge=1, le=20)

# Validation happens automatically
```

### Benefits for Tool Calling

Pydantic automatically generates tool schemas:

```json
{
  "type": "function",
  "function": {
    "name": "search_runbooks",
    "description": "Search runbook database",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string", "minLength": 3, "maxLength": 100},
        "max_results": {"type": "integer", "minimum": 1, "maximum": 20}
      },
      "required": ["query"]
    }
  }
}
```

**LLM sees these constraints** and respects them.

---

## Offline-First: No Cloud APIs

### Decision: Zero Cloud Dependency

**TL;DR:** Privacy, control, and interview credibility.

### Why This Matters
```
Your pitch to recruiter:
"This agent runs entirely locally. 
No data leaves your machine. 
Perfect for enterprise compliance."
```

### Technology Choices That Enable This
| Component | Why Local | Benefit |
|-----------|-----------|---------|
| **Ollama** | Open source LLM runtime | No API keys, full control |
| **ChromaDB** | In-memory vector DB | No external service |
| **Streamlit** | Python framework | Runs on localhost |
| **Pydantic** | Python library | No external calls |

### Alternatives Avoided

#### ❌ Would Break Offline
- OpenAI API (requires internet + API key)
- Pinecone (requires cloud account + internet)
- Weaviate Cloud (requires internet)
- Azure Cognitive Services (requires cloud)

#### ✅ Still Offline
- Any Ollama-compatible API (can point to local or remote)
- Hugging Face transformers (runs locally after download)
- LlamaIndex (uses local LLMs)

### Benefits
- ✅ **Privacy:** No data leaves machine
- ✅ **Compliance:** No cloud concerns
- ✅ **Cost:** Free (no API charges)
- ✅ **Control:** You own the model weights
- ✅ **Offline capable:** Works without internet

### Trade-off
- ❌ **Speed:** Local inference slower than cloud APIs
- ❌ **Cost:** Upfront hardware investment (you provide compute)
- ❌ **Reasoning:** Smaller models = less sophisticated

**For portfolio:** Benefits outweigh trade-offs.

---

## Testing Philosophy: Mock the External Boundary

### Decision: Mock Ollama for Unit Tests, Real DB for Integration

**TL;DR:** Test what you control; mock what you don't.

### The Problem
```python
# ❌ Bad: Tests depend on Ollama running
def test_agent():
    response = react_agent("test query")  # Needs running Ollama
    assert "Found" in response  # Slow, flaky

# ✅ Good: Isolate components
def test_search_validation():
    with pytest.raises(ValidationError):
        search_runbooks(query="x")  # Pydantic validation, fast
    
def test_search_with_real_db():
    collection = seed_runbooks()
    results = search_runbooks("database", collection)
    assert len(results) > 0  # Real ChromaDB, deterministic
```

### Testing Layers

**Layer 1: Unit Tests** (No dependencies)
```python
# test_tools.py
# Mock: everything outside `tools.py`
# Real: Pydantic models, function logic
```

**Layer 2: Integration Tests** (Real DB)
```python
# test_db.py
# Mock: nothing
# Real: ChromaDB, YAML parsing, file I/O
```

**Layer 3: End-to-End** (Real Ollama required)
```python
# test_agent.py (optional, slow)
# Mock: nothing
# Real: Full ReAct loop with running Ollama
```

### Current Test Coverage
```bash
$ pytest tests/ -v

tests/test_db.py: 8/8 PASS      ✅ Data layer
tests/test_tools.py: 15/15 PASS  ✅ Business logic
tests/test_agent.py: (not yet)   ⚠️ End-to-end (requires Ollama)
```

---

## Summary: Design Principles

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **Qwen 2.5-7B** | Recruiter hardware constraints | Speed vs. reasoning depth |
| **Ephemeral ChromaDB** | Zero infrastructure | Single-session only |
| **Streamlit UI** | Fast iteration + beautiful demo | Single-threaded |
| **Pydantic validation** | Automatic schema generation | Slight overhead |
| **Offline-first** | Privacy + control + interview appeal | Speed vs. cloud APIs |
| **Mock-based testing** | Fast, reliable unit tests | E2E tests require Ollama |

---

## Next Steps

- **Learn the architecture:** See [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Get started:** See [GETTING_STARTED.md](./GETTING_STARTED.md)
- **Use programmatically:** See [API.md](./API.md)
