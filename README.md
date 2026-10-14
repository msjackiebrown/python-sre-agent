# 🤖 Python SRE Agent: AI-Powered Incident Troubleshooting

> **Enterprise-Grade Tool-Using AI Agent | Local-First Deployment | ReAct Pattern Implementation**

An **agentic AI system** that reasons through operational incidents, searches a knowledge base of runbooks, and returns actionable solutions—all running locally without cloud dependencies. This is not a chatbot. It's a **decision-making loop** powered by function calling and retrieval-augmented generation (RAG).

**Portfolio Highlights:**
- ✅ **ReAct Pattern**: Reason → Act → Observe cycle for reliable tool calling
- ✅ **Streaming UI**: Streamlit chat interface with proper UX (chronological message flow)
- ✅ **Type-Safe**: Pydantic validation on all tool inputs; type hints throughout
- ✅ **Testable**: Mocked Ollama; ChromaDB operations tested independently
- ✅ **Layered Architecture**: Clean separation of Data/Business/Presentation tiers
- ✅ **OpenAI-Compatible API**: Works with local OR remote Ollama instances

---

## ⚡ Quick Start (5 minutes)

**Requirements:** 8GB+ RAM, Python 3.10+

```bash
# 1. Clone & install
git clone <repo>
cd python-sre-agent
pip install -r requirements.txt

# 2. Run Ollama (if not already running)
ollama run qwen2.5:7b

# 3. Start the UI
streamlit run src/main.py
```

**For remote Ollama:**
```bash
export OLLAMA_HOST=http://api.your-server.com:11434
streamlit run src/main.py
```

Open browser to **`http://localhost:8501`** and start typing incidents.

---

## 🏗️ How It Works: The ReAct Loop

```
User: "Database connection timeouts"
       ↓
LLM (Thinking): "This is a database issue. I should search runbooks."
       ↓
Tool Call: search_runbooks(query="database timeout", max_results=3)
       ↓
ChromaDB Search: Returns [INCIDENT-001, INCIDENT-003, INCIDENT-006]
       ↓
LLM (Synthesis): "Found 3 relevant runbooks. Let me explain the solution..."
       ↓
Response: Formatted runbook details + escalation paths + next steps
```

**Why ReAct matters:** Instead of hallucinating answers, the LLM:
1. **Reasons** about what information is needed
2. **Acts** by calling specific tools (search, validate, fetch)
3. **Observes** real results from those tools
4. **Iterates** up to 5 times to refine the answer

This dramatically reduces hallucinations and grounds answers in actual data.

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **LLM Engine** | [Ollama](https://ollama.com/) (Local) | Runs on consumer hardware; no cloud API calls; full control |
| **Model** | Qwen 2.5-7B (4.7 GB) | Perfect for GitHub + recruiter testing; Qwen 3.8-27B for advanced reasoning |
| **Vector DB** | ChromaDB (In-Memory) | Zero persistence overhead; ephemeral per session; ideal for portfolio projects |
| **Web UI** | Streamlit 1.57+ | Fast iteration; built-in session state; production-ready deployment |
| **Validation** | Pydantic v2 | Type-safe tool arguments; automatic JSON schema generation |
| **Testing** | Pytest | Mock Ollama; test tools independently from LLM |
| **Language** | Python 3.10+ | Type hints throughout; modern async-ready patterns |

---

## 🎯 Architecture: Three Tiers

This project follows **layered architecture**—a hallmark of professional systems:

### **Tier 1: Data Access** (`src/db.py`)
Pure CRUD operations on ChromaDB. Zero business logic.
```python
def add_runbook(collection, runbook_id, document, metadata) → bool
def search_runbooks(collection, query, n_results=3) → list[dict]
def seed_runbooks(data_dir="src/data") → tuple[Collection, int]
```

### **Tier 2: Business Logic** (`src/tools.py`)
Orchestration, validation, file parsing. Knows about Pydantic models and domain rules.
```python
class SearchRunbooksInput(BaseModel):
    query: str = Field(..., min_length=3, max_length=100)
    max_results: int = Field(5, ge=1, le=20)

def search_runbooks(query: str, max_results: int = 5) → str
```

### **Tier 3: Presentation** (`src/agent.py` + `src/main.py`)
- **agent.py**: ReAct loop orchestrator (LLM + tool coordination)
- **main.py**: Streamlit UI (user input/output)

**The Golden Rule:** Each tier only calls the tier below it. Never skip layers.

---

## 📊 Project Status

| Phase | Component | Status | Tests |
|-------|-----------|--------|-------|
| **2** | Data Ingestion (ChromaDB + Runbooks) | ✅ Complete | 8/8 PASS |
| **3** | Tool Setup (Pydantic + Validation) | ✅ Complete | 15/15 PASS |
| **4** | LLM Integration (ReAct Loop + UI) | ✅ Complete | Manual ✓ |
| **5** | API & Optimization | 🔄 Planned | — |

### Data Format: Markdown + YAML Frontmatter

Runbooks stored in `src/data/INCIDENT-*.md` with structured metadata:

```markdown
---
id: INCIDENT-001
title: Database Connection Timeout During Peak Load
severity: high
keywords: database, connection, timeout, pool, exhaustion
contact: db-oncall@company.com
---

## Overview
When traffic spikes, the application's connection pool exhausts...

## Root Cause
Insufficient pool size or slow query responses upstream...

## Resolution Steps
1. SSH into the database server
2. Check active connections: `SELECT count(*) FROM pg_stat_activity`
3. Adjust pool settings in the application config
4. Monitor for recovery within 2 minutes
```

---

## 🧪 Testing & Code Quality

### Test Coverage
Run tests with:
```bash
pytest tests/ -v
```

**Test Results:**
- ✅ **Data Layer** (`test_db.py`): 8/8 PASS
  - YAML frontmatter parsing (normal, missing, empty, multiline values)
  - Runbook seeding (counts, metadata, file type filtering)
  - Edge cases (numeric values, quoted strings)

- ✅ **Business Logic** (`test_tools.py`): 15/15 PASS
  - Pydantic validation (boundaries, required fields, type coercion)
  - Error handling (invalid input, no results, tool failures)
  - Integration tests (mocked + real ChromaDB operations)

**Test Philosophy:** Mocked Ollama for tool testing; tools never depend on running LLM.

### Type Safety
```bash
# All files use type hints
python -m mypy src/
```

**Key patterns:**
- Pydantic `BaseModel` for input validation
- Return type annotations on all functions
- `type: ignore` only where necessary (with comments)

---

## 🔌 Ollama Integration: OpenAI-Compatible API

This agent uses Ollama's OpenAI-compatible REST API, which means:

**Local Setup:**
```bash
ollama run qwen2.5:7b
# Creates HTTP endpoint at http://localhost:11434
```

**Remote Setup:**
```bash
export OLLAMA_HOST=http://api.your-server.com:11434
export OLLAMA_MODEL=qwen2.5:7b
streamlit run src/main.py
```

The `ollama` Python library respects `OLLAMA_HOST` environment variable automatically—no code changes needed.

### Function Calling Flow
```
1. Agent calls: chat(model="qwen2.5:7b", tools=[search_runbooks], ...)
2. Ollama introspects search_runbooks() function:
   - Docstring → tool description
   - Parameters → JSON schema
3. LLM decides to call: {"function": "search_runbooks", "arguments": {...}}
4. Python intercepts, validates with Pydantic, executes
5. Result injected back into conversation history
6. LLM synthesizes final answer grounded in real data
```

---

## 💡 Key Design Decisions

### 1. **Model Selection: Qwen 2.5-7B for Portfolio**
- ✅ Runs on 8GB consumer hardware (recruiter-friendly)
- ✅ Fast inference (50+ tokens/sec on CPU)
- ✅ Tool calling reliability matches larger models
- 📺 Optional: Use Qwen 3.8-27B for YouTube demo (visible reasoning)

**Rationale:** Recruiters will clone and test this. Make it "just works."

### 2. **Ephemeral ChromaDB (No Persistence)**
- ✅ Zero external dependencies (no database server)
- ✅ Session scoped (clean state per run)
- ✅ Perfect for portfolio projects (no DevOps overhead)
- 🏭 Production: Use persistent ChromaDB or vector database

### 3. **Layered Architecture**
Strictly enforced:
```
Streamlit UI  →  ReAct Agent  →  Pydantic Tools  →  ChromaDB
    (Layer 3)      (Layer 3)        (Layer 2)       (Layer 1)
```

**Benefit:** Easy to swap layers. Replace Streamlit with FastAPI; replace ChromaDB with Pinecone—without touching agent logic.

### 4. **Type Hints Everywhere**
```python
def react_agent(user_query: str, max_iterations: int = 5, verbose: bool = False) → str:
    """Reason → Act → Observe loop with safety bounds."""
```

**Benefit:** Self-documenting code. Enables IDE autocomplete and type checking.

### 5. **Offline-First, No Cloud APIs**
- ✅ Ollama runs locally
- ✅ ChromaDB in-memory
- ✅ All computation stays on localhost
- 🎯 Perfect for portfolio: Shows you understand privacy and deployment constraints

---

## 📁 Project Structure

```
python-sre-agent/
├── src/
│   ├── agent.py          # ReAct loop + Ollama connection
│   ├── main.py           # Streamlit UI
│   ├── tools.py          # Search_runbooks + Pydantic validation
│   ├── db.py             # ChromaDB CRUD operations
│   └── data/
│       ├── INCIDENT-001.md  # Sample runbooks (7 total)
│       └── ...
├── tests/
│   ├── test_db.py        # Data layer tests (8 tests)
│   ├── test_tools.py     # Business logic tests (15 tests)
│   └── conftest.py       # Pytest fixtures
├── notes/                # Portfolio preparation docs (not for recruiters)
│   ├── REACT-PATTERN.md
│   ├── OLLAMA-API-REFERENCE.md
│   ├── layered-architecture-pattern.md
│   └── ...
├── requirements.txt
├── README.md
├── AGENTS.md             # Coding standards + governance
└── PROJECT_GUIDE.md      # Architecture deep-dive
```

---

## 🚀 Running the Agent

### Option 1: Interactive Chat UI (Recommended)
```bash
streamlit run src/main.py
```
Opens a browser to `http://localhost:8501` with a chat interface.

**Features:**
- ✅ Chronological message display (newest at bottom, like Slack)
- ✅ Connection status in sidebar
- ✅ Clear conversation history button
- ✅ Expandable help panels
- ✅ Auto-scrolls to new messages

### Option 2: Direct Agent Loop (Testing/Debugging)
```bash
python src/agent.py
```

Runs 3 test queries through the ReAct agent and prints verbose iteration info.

### Option 3: Programmatic Use
```python
from agent import react_agent

response = react_agent("Database connection timeouts", max_iterations=5, verbose=True)
print(response)
```

---

## 🧠 How the Agent Reasons

Example trace with `verbose=True`:

```
🔄 Iteration 1/5
   LLM Response: I should search for runbooks about database issues...
   → Tool call: search_runbooks(query='database timeout', max_results=3)
   ← Result: ✅ Found 3 runbooks (IDs: 001, 003, 006)

🔄 Iteration 2/5
   LLM Response: These runbooks cover connection pools and timeout settings.
   Let me format the solution for the user...
   
   → No more tool calls. Returning final answer.

🤖 Agent Response:
I found 3 runbooks related to database timeouts. Here are the key steps...
[Full runbook details with severity, escalation, next steps]
```

The agent will iterate up to 5 times, searching for more information or refining answers based on tool results.

---

## 🔐 Security & Privacy

- ✅ **No cloud APIs**: All data stays on localhost
- ✅ **No API keys**: No external credentials needed
- ✅ **No persistence**: Session data cleared on exit
- ✅ **Mocked data**: All runbooks are synthetic (no real PII)
- ✅ **Type validation**: Pydantic ensures safe tool arguments

Perfect for enterprise demonstrations without compliance concerns.

---

## 📚 Documentation

- **[AGENTS.md](./AGENTS.md)**: Project governance, coding standards, development gates
- **[PROJECT_GUIDE.md](./PROJECT_GUIDE.md)**: Architecture blueprint, design patterns, learning resources
- **[notes/OLLAMA-API-REFERENCE.md](./notes/OLLAMA-API-REFERENCE.md)**: Ollama REST API reference (curl + Python)
- **[notes/REACT-PATTERN.md](./notes/REACT-PATTERN.md)**: Deep dive into the ReAct pattern
- **[notes/layered-architecture-pattern.md](./notes/layered-architecture-pattern.md)**: Why and how to structure your code in 3 tiers

---

## 🤔 Interview Questions You Should Be Ready For

### Architecture
- *"Why a ReAct loop instead of just asking the LLM?"* → Reduces hallucinations by grounding in tool results
- *"Why ChromaDB and not Pinecone?"* → Portfolio projects should run locally; Pinecone for production
- *"Why separate db.py from tools.py?"* → Layered architecture; each tier has one job

### Ollama & LLMs
- *"How does function calling work?"* → Ollama introspects Python functions, generates JSON schema, intercepts tool calls
- *"Why Qwen 2.5-7B?"* → Recruiter hardware constraints; fast inference; tool calling reliability
- *"How would you handle a tool failure?"* → Catch exception, return error string, LLM retries or explains failure

### Testing & Code Quality
- *"How do you test without a running Ollama?"* → Mock the ollama.chat() function in unit tests
- *"What if a tool returns unexpected data?"* → Pydantic validation + explicit error messages
- *"How would you scale this?"* → FastAPI instead of Streamlit; Redis for session management; persistent vector DB

---

## 🎯 Next Steps & Phase 5

**Planned enhancements:**
- FastAPI wrapper for API-first deployment
- Performance optimization (batching, async)
- Extended runbook library (20+ incidents)
- Metrics & logging (response time, tool call success rate)
- Kubernetes deployment examples

---

## 📝 License

This project is provided as-is for portfolio demonstration purposes.

---

## 👤 Author

**Note:** This is a demonstration project showcasing modern LLM patterns (ReAct, tool calling, RAG) and clean software architecture for SRE automation. Built with a focus on local-first deployment and interview readiness.
