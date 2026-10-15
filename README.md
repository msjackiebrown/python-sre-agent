# 🤖 Python SRE Agent

> **Local-First AI Agent | ReAct Pattern | Tool Calling + RAG**

An **agentic AI system** that uses a Reason→Act→Observe loop to troubleshoot operational incidents, search a runbook knowledge base, and deliver actionable solutions—all on your laptop, no cloud required.

**What makes this portfolio-ready:**
- ✅ **ReAct Loop:** Reduces LLM hallucination by grounding answers in real tool results
- ✅ **Function Calling:** LLM safely invokes Python functions via OpenAI-compatible API
- ✅ **Retrieval-Augmented Generation:** Semantic search over incident runbooks
- ✅ **Layered Architecture:** Clean separation of Data/Business/UI tiers
- ✅ **Type-Safe:** Pydantic validation + type hints throughout
- ✅ **Tested:** 23 unit + integration tests; mocked external dependencies
- ✅ **Production-Ready UI:** Streamlit chat interface with proper UX

---

## ⚡ Quick Start (5 minutes)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Run Ollama (separate terminal)
ollama run qwen2.5:7b

# 3. Start UI
streamlit run src/main.py
# Opens http://localhost:8501
```

**For remote Ollama:**
```bash
export OLLAMA_HOST=http://your-server:11434
streamlit run src/main.py
```

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **[docs/GETTING_STARTED.md](./docs/GETTING_STARTED.md)** | Installation, setup, first run |
| **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** | System design, ReAct loop, 3-tier model |
| **[docs/DESIGN_DECISIONS.md](./docs/DESIGN_DECISIONS.md)** | Why each tech choice (with trade-offs) |
| **[docs/API.md](./docs/API.md)** | Programmatic usage, function signatures |
| **[docs/TESTING.md](./docs/TESTING.md)** | Test strategy, how to run tests |
| **[docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)** | Docker, Kubernetes, cloud platforms |

---

## 🎯 Project at a Glance

**Tech Stack:**
- **LLM:** Ollama + Qwen 2.5-7B (4.7GB)
- **Vector DB:** ChromaDB (in-memory, ephemeral)
- **UI:** Streamlit
- **Validation:** Pydantic v2
- **Language:** Python 3.10+ (typed)

**Architecture:**
```
Layer 3: Streamlit UI (src/main.py)
    ↓
Layer 2: ReAct Agent (src/agent.py) + Tools (src/tools.py)
    ↓
Layer 1: Database (src/db.py) + ChromaDB
```

**Current Status:**
- Phase 2 (Data) ✅ — 8/8 tests passing
- Phase 3 (Tools) ✅ — 15/15 tests passing  
- Phase 4 (LLM + UI) ✅ — Manual testing complete
- Phase 5 (Scaling) 🔄 — Planned

---

## 🤔 Common Questions

**Why ReAct instead of just prompting the LLM?**
→ Reduces hallucinations by making the LLM search real data before answering.

**Why Qwen 2.5-7B?**
→ Fits on recruiter laptops (8GB RAM), tool calling works great, inference is fast (~50 tok/sec).

**Why ChromaDB and not Pinecone?**
→ Portfolio projects should "just work" locally. Zero infrastructure, zero API keys.

**How does function calling work?**
→ Ollama introspects your Python function (docstring, parameters), generates JSON schema, intercepts LLM's tool calls, validates with Pydantic, executes.

**How do you test without Ollama running?**
→ Mock the `ollama.chat()` function. Tools are tested independently via unit tests.

**For production, what would you change?**
→ FastAPI instead of Streamlit. Persistent vector DB (Weaviate/Pinecone). Async/concurrent tool calls. Monitoring/logging. See [DEPLOYMENT.md](./docs/DEPLOYMENT.md).

---

## 📁 Files

```
src/
├── agent.py        # ReAct loop orchestrator + Ollama connection
├── main.py         # Streamlit UI
├── tools.py        # search_runbooks() + Pydantic validation
├── db.py           # ChromaDB CRUD operations
└── data/           # 7 sample incident runbooks (INCIDENT-*.md)

tests/
├── test_db.py      # Data layer (8 tests)
├── test_tools.py   # Business logic (15 tests)
└── conftest.py     # Pytest fixtures

docs/               # Detailed documentation (you are here!)
notes/              # Learning materials (for your reference, not recruiters)
```

---

## 🚀 Running

### Web UI (Recommended)
```bash
streamlit run src/main.py
# Chat interface at http://localhost:8501
```

### CLI (Debug)
```bash
python src/agent.py
# Runs 3 test queries with verbose output
```

### Python API
```python
from src.agent import react_agent
response = react_agent("Database timeout")
print(response)
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Expected: 23 passed

# Data layer only
pytest tests/test_db.py -v

# Business logic only
pytest tests/test_tools.py -v
```

---

## 🔒 Security & Privacy

- ✅ No cloud APIs (data stays on localhost)
- ✅ No API keys needed
- ✅ No external authentication
- ✅ Ephemeral data (cleared on exit)
- ✅ Type validation prevents injection

Perfect for enterprise + compliance.

---

## 📚 Learning Path

1. **Start here:** [GETTING_STARTED.md](./docs/GETTING_STARTED.md)
2. **Understand the design:** [ARCHITECTURE.md](./docs/ARCHITECTURE.md)
3. **Learn why we chose each tech:** [DESIGN_DECISIONS.md](./docs/DESIGN_DECISIONS.md)
4. **Use as a library:** [API.md](./docs/API.md)
5. **Write tests:** [TESTING.md](./docs/TESTING.md)
6. **Deploy:** [DEPLOYMENT.md](./docs/DEPLOYMENT.md)

---

## 💡 Interview Prep

You should be ready to explain:
- ✅ What is the ReAct pattern and why does it help?
- ✅ How does Ollama's function calling work?
- ✅ Why this 3-tier architecture?
- ✅ Why Pydantic for validation?
- ✅ How to test without external dependencies?
- ✅ Trade-offs: local vs. cloud, ephemeral vs. persistent, etc.

All answers are documented in the `docs/` folder.

---

## 📝 License

Portfolio demonstration project. Use freely for learning.

---

**Next:** Read [docs/GETTING_STARTED.md](./docs/GETTING_STARTED.md) to install and run.

**Questions?** Check [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for deep dives, or [docs/DESIGN_DECISIONS.md](./docs/DESIGN_DECISIONS.md) for the "why" behind each choice.
