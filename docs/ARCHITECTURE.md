# Architecture: System Design & Patterns

Deep dive into how the SRE Agent is structured and why.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                     │
│                  (Streamlit Web UI / CLI)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   AGENT ORCHESTRATION LAYER                  │
│              (ReAct Loop + LLM Coordination)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
    ┌─────────┐  ┌──────────┐  ┌──────────────┐
    │ Ollama  │  │ Pydantic │  │ ChromaDB     │
    │ LLM API │  │ Validator│  │ Vector DB    │
    │(Function│  │          │  │              │
    │Calling) │  │          │  │              │
    └─────────┘  └──────────┘  └──────────────┘
```

---

## Three-Tier Architecture

The entire system follows **layered architecture** for clean separation of concerns:

### **Tier 3: Presentation** (`src/main.py` + `src/agent.py`)

**Responsibility:** User input/output and orchestration

**Files:**
- `src/main.py` — Streamlit UI
- `src/agent.py` — ReAct loop orchestrator

**What it does:**
- Accepts user queries (chat input, CLI args, API requests)
- Calls the ReAct agent
- Displays results with formatting
- Manages conversation history

**Key insight:** Never talks directly to ChromaDB. Always goes through lower tiers.

---

### **Tier 2: Business Logic** (`src/tools.py` + `src/agent.py`)

**Responsibility:** Domain logic, orchestration, validation

**Files:**
- `src/tools.py` — Tool definitions and Pydantic models
- `src/agent.py` — ReAct loop (part of this tier too)

**What it does:**
- Defines `SearchRunbooksInput` Pydantic model
- Validates tool arguments automatically
- Searches runbooks with error handling
- Manages tool execution within ReAct loop
- Returns structured results

**Key insight:** Knows about business rules (runbook format, search keywords) but doesn't directly access storage.

---

### **Tier 1: Data Access** (`src/db.py`)

**Responsibility:** Pure CRUD on ChromaDB

**Files:**
- `src/db.py` — All database operations

**What it does:**
```python
def init_collection(collection_name="runbooks", space="cosine"):
    """Create ChromaDB collection"""

def add_runbook(collection, runbook_id, document, metadata):
    """Insert one runbook"""

def search_runbooks(collection, query, n_results=3):
    """Vector search (returns top N matches)"""

def seed_runbooks(data_dir="src/data"):
    """Bulk load all .md files"""
```

**Key insight:** Zero knowledge of business logic. Just does what it's asked.

---

## The ReAct Loop: How Reasoning Works

**ReAct** = **Re**asoning + **Act**ing

```
┌──────────────────────────────────────┐
│  USER QUERY                          │
│  "Database connection timeout"       │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  THOUGHT (LLM Reasoning)             │
│  "This is a database issue.          │
│   I need to search runbooks."        │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  ACTION (Tool Call)                  │
│  search_runbooks(                    │
│    query="database timeout",         │
│    max_results=3                     │
│  )                                   │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  OBSERVATION (Tool Result)           │
│  ✅ Found 3 runbooks:                │
│     - INCIDENT-001 (High)            │
│     - INCIDENT-003 (Medium)          │
│     - INCIDENT-006 (Medium)          │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  REASONING (LLM Analyzes)            │
│  "These cover connection pools,      │
│   timeout settings, and monitoring.  │
│   Let me format for the user..."     │
└──────────────┬───────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
    More tools?   Final answer?
        │             │
       YES           NO
        │             │
        └─→ Loop ←────┘
            (max 5 iterations)
             │
             ▼
         ┌─────────────┐
         │   RESPONSE  │
         │  (to user)  │
         └─────────────┘
```

### Key Properties:
- **Safety:** Bounded by `max_iterations=5`
- **Grounding:** Results come from tool calls, not LLM hallucinations
- **Transparency:** Each iteration is logged (if `verbose=True`)
- **Graceful Degradation:** If tool fails, LLM gets error message and can retry

---

## Function Calling: How the LLM Calls Python

When you call:
```python
response = chat(
    model="qwen2.5:7b",
    messages=[...],
    tools=[search_runbooks],  # ← Pass Python function directly!
    stream=False
)
```

Ollama's OpenAI-compatible API does this:

1. **Introspect the function:**
   ```python
   def search_runbooks(query: str, max_results: int = 5) -> str:
       """Search the runbook database by keyword."""
   ```

2. **Generate JSON schema:**
   ```json
   {
     "type": "function",
     "function": {
       "name": "search_runbooks",
       "description": "Search the runbook database by keyword.",
       "parameters": {
         "type": "object",
         "properties": {
           "query": {"type": "string"},
           "max_results": {"type": "integer"}
         },
         "required": ["query"]
       }
     }
   }
   ```

3. **LLM decides to call it:**
   ```json
   {
     "tool_calls": [
       {
         "function": {
           "name": "search_runbooks",
           "arguments": {
             "query": "database timeout",
             "max_results": 3
           }
         }
       }
     ]
   }
   ```

4. **Python intercepts and validates:**
   ```python
   # Pydantic validates the arguments
   validated_args = SearchRunbooksInput(
       query="database timeout",
       max_results=3
   )
   ```

5. **Execute the tool:**
   ```python
   result = search_runbooks(**validated_args.dict())
   # Returns: "✅ Found 3 matching runbooks..."
   ```

6. **Inject back into conversation:**
   ```python
   messages.append({
       "role": "tool",
       "tool_name": "search_runbooks",
       "content": result
   })
   ```

7. **LLM synthesizes final answer** grounded in real data.

**Key insight:** No manual JSON schema needed. Just pass Python functions.

---

## Data Flow: Query to Answer

```
User Input (Streamlit)
    │
    ▼
react_agent(query)
    │
    ├─→ Initialize messages [system_prompt, user_query]
    │
    ├─→ While iteration < max_iterations:
    │   │
    │   ├─→ chat(model, messages, tools=[search_runbooks])
    │   │   │ (Ollama LLM decides if tool is needed)
    │   │
    │   ├─→ If LLM calls tool:
    │   │   │
    │   │   ├─→ Extract function name & arguments
    │   │   │
    │   │   ├─→ Pydantic validates arguments
    │   │   │   └─→ SearchRunbooksInput
    │   │   │
    │   │   ├─→ Execute: search_runbooks(query, max_results)
    │   │   │   │
    │   │   │   ├─→ Get ChromaDB collection
    │   │   │   │
    │   │   │   ├─→ collection.query(query_text, n_results)
    │   │   │   │   └─→ Vector similarity search
    │   │   │   │
    │   │   │   └─→ Format results with severity, escalation
    │   │   │
    │   │   └─→ Add tool result to messages
    │   │       {"role": "tool", "content": result}
    │   │
    │   └─→ If no tool calls → Return response.message.content
    │
    └─→ Return formatted answer

Display in Streamlit UI
    │
    └─→ Chat message box
```

---

## Error Handling: What Happens When Things Break

### Tool Validation Error
```python
# User (via LLM) tries: search_runbooks(query="x")
# → Validation fails: query too short (min 3 chars)

# Graceful handling:
try:
    result = search_runbooks(**tool_args)
except ValidationError as e:
    result = f"❌ Invalid arguments: {e}"
    # LLM sees error, can retry with better args
```

### No Matching Runbooks
```python
# LLM: search_runbooks(query="obscure-topic-never-indexed")
# → ChromaDB returns empty list

# Agent returns:
"❌ No matching runbooks found for 'obscure-topic'"

# LLM can retry with different keywords
```

### Max Iterations Reached
```python
# Agent loops 5 times without conclusion
# → Return last response with warning

⚠️ Max iterations (5) reached. Last response: ...
```

### LLM Doesn't Call Any Tools
```python
# LLM decides: "I can answer this without tools"
# → Return response immediately (exit loop)

Agent Response: [LLM's direct answer]
```

---

## Technology Choices & Trade-offs

### Why Ollama?
- ✅ Runs locally (no cloud dependencies)
- ✅ OpenAI-compatible API (easy to swap providers)
- ✅ Function calling support (via tool parameters)
- ✅ Model flexibility (swap qwen2.5:7b for llama2 anytime)
- ❌ Slower than cloud APIs (trade-off: privacy + control)

### Why Qwen 2.5-7B?
- ✅ 4.7 GB (fits in 8GB RAM)
- ✅ Tool calling reliability
- ✅ Fast inference (50+ tokens/sec on CPU)
- ✅ Recruiter-friendly (can actually run it)
- ❌ Limited reasoning depth vs. larger models
- 💡 Qwen 3.8-27B available for advanced scenarios

### Why ChromaDB?
- ✅ In-memory (ephemeral, no persistence)
- ✅ Semantic search (vector similarity, not keyword)
- ✅ Zero external dependencies (perfect for portfolios)
- ❌ Not suitable for production (use Pinecone/Weaviate instead)

### Why Streamlit?
- ✅ Zero DevOps (runs locally or on Streamlit Cloud)
- ✅ Session state management built-in
- ✅ Fast iteration on UI changes
- ❌ Not ideal for high-traffic APIs (use FastAPI instead)

### Why Pydantic?
- ✅ Automatic JSON schema generation (for tool calling)
- ✅ Type validation at runtime
- ✅ Clear error messages
- ✅ Integrates seamlessly with FastAPI

---

## Scalability Considerations

### Current Architecture
- Single-threaded ReAct loop
- Ephemeral ChromaDB (recreated per session)
- 7 sample runbooks

### For Production (Phase 5+)
```
Tier 1: FastAPI (replaces Streamlit)
    ↓
Tier 2: ReAct agent (unchanged)
    + Add async/await for concurrent tool calls
    + Add request queuing & rate limiting
    ↓
Tier 1: PostgreSQL + Weaviate (replaces ChromaDB)
    + Persistent runbook storage
    + Distributed vector search
    + Multi-user support
```

### Database Scalability
| Scenario | Current | Recommended |
|----------|---------|-------------|
| **Single user, local** | ChromaDB in-memory | ✅ Current setup |
| **Multiple users, local** | ChromaDB persistent | ChromaDB SQLite backend |
| **Deployed to cloud** | ChromaDB + S3 | Weaviate / Pinecone |
| **Enterprise scale** | — | Weaviate Kubernetes cluster |

---

## Security Model

### What's Protected
- ✅ No external APIs (no leaked API keys)
- ✅ No cloud logging (data stays local)
- ✅ Type validation (prevents injection attacks)
- ✅ Tool sandboxing (LLM can only call pre-defined tools)

### What's NOT Protected
- ❌ No authentication (local development only)
- ❌ No encryption (in-memory, not persisted)
- ❌ No rate limiting (untested under load)

For production, add:
- OAuth2 / JWT authentication
- TLS encryption
- Request rate limiting
- Audit logging

---

## Testing Strategy

### Unit Tests (Mocked)
```python
# Don't need running Ollama
def test_search_runbooks_validation():
    with pytest.raises(ValidationError):
        search_runbooks(query="x")  # Too short
```

### Integration Tests (Real ChromaDB)
```python
# Test data access + business logic together
def test_seed_and_search():
    collection, count = seed_runbooks()
    assert count == 7
    results = search_runbooks("database", max_results=3)
    assert len(results) > 0
```

### End-to-End Tests (Full System)
```python
# Test agent loop (requires running Ollama)
def test_react_loop_with_real_ollama():
    response = react_agent("Database timeout")
    assert "INCIDENT" in response
    assert "Found" in response or "Error" in response
```

See [TESTING.md](./TESTING.md) for details.

---

## Next Steps

- **Learn how to use:** See [GETTING_STARTED.md](./GETTING_STARTED.md)
- **Understand design:** See [DESIGN_DECISIONS.md](./DESIGN_DECISIONS.md)
- **Use programmatically:** See [API.md](./API.md)
- **Deploy:** See [DEPLOYMENT.md](./DEPLOYMENT.md)
