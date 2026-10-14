# 📘 PROJECT GUIDE: Building a Tool-Using Agent

This guide contains the architectural concepts, resources, and critical design questions you need to answer as you implement the `python-sre-agent`. 

## 1. Layered Architecture: Data → Tools → LLM → API → UI

You are building an **Agent**, not just a Chatbot. A chatbot asks/answers. An Agent *Reasons*, *Acts* (calls tools), and then *Observes* the result.

**Architecture Diagram (Bottom-Up Design):**
```
┌──────────────────────────────────────────────┐
│  UI Layer (Phase 6)                          │
│  Streamlit web interface                     │
│  "User talks to chatbot"                     │
└─────────────────┬────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│  API/Interface Layer (Phase 5)               │
│  Testing, formatting, CLI wrapper            │
│  "Ensure everything works together"          │
└─────────────────┬────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│  Application Layer (Phase 4)                 │
│  ReAct loop + Ollama tool calling            │
│  "Reason → Act → Observe → Answer"           │
└─────────────────┬────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│  Business Logic Layer (Phase 3)              │
│  Tools with Pydantic validation              │
│  "Safe, validated operations"                │
└─────────────────┬────────────────────────────┘
                  ↓
┌──────────────────────────────────────────────┐
│  Data Layer (Phase 2)                        │
│  ChromaDB + 7 mock runbooks                  │
│  "Semantic search, retrieval"                │
└──────────────────────────────────────────────┘
```

**Implementation order (Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6):**
1. **Phase 2 — Data Layer:** Get ChromaDB working with 7 runbooks loaded
2. **Phase 3 — Business Logic Layer:** Build `search_runbooks()` with Pydantic validation
3. **Phase 4 — Application Layer:** Hook it all up with Ollama tool calling (ReAct loop)
4. **Phase 5 — API/Interface Layer:** Test suite + CLI verification
5. **Phase 6 — Presentation Layer:** Streamlit UI (thin wrapper around proven backend)

**Runtime flow (what happens when user asks):**
1.  **User Input:** "Why is the SWIFT API timing out?"
2.  **LLM Thought:** *"I don't know, but I have a tool called `search_runbooks`."* → Returns JSON schema.
3.  **Python Code:** Intercepts JSON → Runs `search_runbooks()` against ChromaDB → Gets result.
4.  **Tool Result:** Injected back into LLM context as `<tool_response> ... </tool_response>`.
5.  **Final Answer:** LLM synthesizes the text using that data.
6.  **UI Display:** Streamlit renders the response to user.

## 2. Key Resources to Study
- **[Ollama Tool Calling Docs](https://docs.ollama.com/capabilities/tool-calling#python):** *Critical.* Read how `chat_request.messages[].tool_calls` works in the raw JSON response. This is where your branching logic lives.
- **[ChromaDB Quickstart (In-Memory)](https://www.trychroma.com/docs/embeddings/overview):** Look for `chromadb.Client()` vs `chromadb.PersistentClient()`. You want the first one.
- **[LangChain Tool Calling Tutorials](https://python.langchain.com/docs/how_to/#tools):** Even though we aren't using LangChain, their *diagrams* of how agents handle tool outputs are excellent for understanding the pattern.

## 2. Implementation Order: Data → Tools → LLM

### Phase 2: DATA INGESTION (Do This First!)
**Goal:** Get ChromaDB working with 7 mock runbooks

**Questions to answer:**
- **Q1: Runbook Format** — What metadata matters? (title, steps, contact, escalate)
- **Q2: Embedding Strategy** — Bulk-load all runbooks at startup (recommended) or on-demand?
- **Q3: Search Quality** — Are semantic matches good enough, or do we need keyword filtering?

**Deliverables:**
- `src/data/INCIDENT-001.md` through `INCIDENT-007.md` (7 realistic runbooks)
- `src/runbook_db.py` with `RunbookDatabase` class
- Proof: `python src/runbook_db.py` → Seeds 7 runbooks, searches work

### Phase 3: TOOL LAYER (Once Data is Solid)
**Goal:** Build tools that safely query your data

**Questions to answer:**
- **Q1: Tool Schema Precision** — How strictly defined? Force incident-only keywords?
- **Q2: Validation** — Use Pydantic to catch bad LLM arguments (empty query, out of range)
- **Q3: Error Handling** — Return error strings to LLM, never crash

**Deliverables:**
- `src/tools.py` with `SearchRunbooksInput` (Pydantic model) + `search_runbooks()` function
- Unit tests: valid queries, empty queries, out-of-range args
- Proof: `pytest tests/test_tools.py` → All pass

### Phase 4: LLM LAYER (Wire It All Together)
**Goal:** Hook up Ollama tool calling

**Questions to answer:**
- **Q1: The "Max Iterations" Trap** — Prevent infinite tool loops (implement counter, max=3)
- **Q2: Tool Result Injection** — Format results for LLM context
- **Q3: Fallback Response** — What if no runbook matches after 3 tries?

**Deliverables:**
- `src/agent.py` with ReAct loop + tool calling
- Integration tests: Qwen 2.5-7B + ChromaDB + Ollama
- Proof: `python src/agent.py "database timeout"` → Returns relevant runbook

### Phase 5: API & TESTING (Quality Assurance)
**Goal:** Ensure everything works together + prepare for multiple interfaces

**Questions to answer:**
- **Q1: Test Coverage** — What tests matter? (unit, integration, end-to-end)
- **Q2: CLI vs API** — Simple CLI wrapper or full REST API?
- **Q3: Error Handling** — What happens when ChromaDB is down? Ollama offline?

**Deliverables:**
- `tests/` directory with full test suite
- `src/cli.py` (simple CLI wrapper for testing)
- CI/CD pipeline (`pytest`, `ruff check`)
- Proof: `pytest tests/` → All pass, 80%+ coverage

### Phase 6: UI LAYER (Presentation)
**Goal:** Add Streamlit interface as thin wrapper around proven backend

**Why UI comes LAST:**
- ✅ Backend is stable (Phases 2-5)
- ✅ Core logic proven in tests
- ✅ UI is replaceable, backend is solid
- ✅ Streamlit is just a wrapper, not core logic

**Questions to answer:**
- **Q1: UI Design** — Simple form + response display, or fancy chat interface?
- **Q2: Session State** — Track conversation history or one-shot queries only?
- **Q3: Error Display** — How to show errors to users?

**Deliverables:**
- `src/ui.py` with Streamlit app
  ```python
  import streamlit as st
  from agent import run_agent_loop
  
  st.title("🤖 SRE Agent - Runbook Search")
  user_query = st.text_input("Describe your incident:")
  if st.button("Search Runbooks"):
      response = run_agent_loop(user_query)
      st.markdown(response)
  ```
- Proof: `streamlit run src/ui.py` → UI loads, queries work, results display

## 3. Why This Order? (Risk Reduction Rationale)

**DON'T do this (the old way):**
```
UI First → Backend to match UI → Tools → ChromaDB
→ Disaster: UI is locked in, everything below is fragile
```

**DO do this (layered architecture):**
```
Data → Tools → LLM → API → UI
(Each layer testable independently, UI is replaceable)
```

### Risk Matrix: Why Bottom-Up?

| Phase | Build | Can Test Without? | If This Breaks | Cost to Fix |
| :--- | :--- | :--- | :--- | :--- |
| 2 (Data) | ChromaDB | Anything | All of it | Low (just data) |
| 3 (Tools) | Validation | LLM | All of it | Medium (redo tools) |
| 4 (LLM) | Agent loop | UI | Queries fail | Medium (debug LLM) |
| 5 (API) | Tests & CLI | UI | No safety net | Low (add tests) |
| 6 (UI) | Streamlit | Nothing | User sees errors | High! (UX broken) |

**Key insight:** If you build UI first and Phase 2 breaks, your UI is now useless. If you build Phase 2 first and UI breaks, your agent still works via CLI.

### Test Commands (Proof at Each Phase)

```bash
# Phase 2: Data works
python src/runbook_db.py
# Output: ✅ Seeded 7 runbooks, search returns INCIDENT-001

# Phase 3: Tools validated
pytest tests/test_tools.py
# Output: ✅ All validation tests pass

# Phase 4: Agent + LLM integrated
python src/agent.py "database timeout"
# Output: ✅ Agent returns runbook + explanation

# Phase 5: Everything together
pytest tests/
# Output: ✅ 100% suite pass, CI/CD green

# Phase 6: UI works
streamlit run src/ui.py
# Output: 🎯 Web interface loads, queries work, results display
```

### Interview Story (Why UI Last?)

> "I build using **layered architecture**. Data → Tools → LLM → API → UI. Why? Risk reduction. If data breaks, only data is affected. If UI breaks, only the presentation is affected—the agent still works via CLI. This is how production systems scale: stable layers first, pretty UI second. Recruiters love this answer because it shows you've thought about maintainability."

---

## 4. Portfolio "Flex" Points (Why this gets hired)
1. **Local Inference:** You prove you can build complex AI apps without $50/mo API bills.
2. **Tool Safety:** By catching JSON errors and tool failures, you show you write *production-ready* code, not just playground scripts.
3. **Domain Expertise:** The mock data proves you understand *Enterprise SRE workflows* (SWIFT, PCI-DSS), bridging the gap between AI dev and Business Ops.
4. **Layered Architecture:** Shows you think in layers (data → tools → integration), not monolithic "build it all at once"

---

**Current Status:** Phase 2 (Data Ingestion) — Implement `src/runbook_db.py` first, prove it works, then build Phase 3 tools.