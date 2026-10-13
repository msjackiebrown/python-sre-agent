# 🏗️ AGENTS.md - Governance & Development Standards

## Project: Python SRE Agent (Tool-Using Chatbot)
**Goal:** Build a local-first AI assistant that uses Ollama Function Calling to interact with mocked infrastructure tools and a ChromaDB runbook knowledge base.
**Status:** Phase 2 (Design & Architecture) → Phase 3 (Implementation)

---

## 🚧 Stack Rules & Standards

### 1. Tech Stack Constraints
- **Language:** Python 3.10+ (Typed, `type: ignore` only where necessary).
- **LLM Engine:** Ollama (Local only). No Cloud API calls allowed without explicit "Cloud Justification Report" in an ADR.
- **Vector Store:** ChromaDB (In-Memory mode for this specific repo to ensure zero-dependency portability for portfolio reviews).
- **Runtime:** Must run on standard consumer hardware (e.g., 8GB+ RAM, integrated graphics). Optimize inference calls to keep CPU/RAM usage low.

### 2. Coding Standards
- **Linting:** `ruff check src/` (Target PEP 8 with type hints).
- **Testing:** `pytest tests/`. All tools must be unit-testable without a running LLM backend (mock the `ollama` client).
- **Directory Structure:**
    - `src/agent.py`: The core ReAct loop.
    - `src/tools.py`: Pure functions that perform actions.
    - `src/data/`: Mock runbooks and vector seeding logic.

### 3. Tool Calling Design
- All tool schemas MUST match Ollama's expected JSON format.
- **Error Handling:** Tools must catch exceptions (e.g., NetworkError) and return a structured string error to the LLM, allowing it to retry or explain failure, rather than crashing the agent loop.

---

## ⏱️ Phase Gates

| Phase | Goal | Status |
| :--- | :--- | :--- |
| **Phase 1** | Governance & Repo Setup | ✅ Done |
| **Phase 2** | Define Tool Schemas & Mock Data Schema | 🔄 In Progress |
| **Phase 3** | Build Agent Loop (Ollama streaming + logic) | ⬜ Pending |
| **Phase 4** | Integrate ChromaDB Runbook Search Tool | ⬜ Pending |
| **Phase 5** | CI/CD, Testing & Documentation Polish | ⬜ Pending |

---

## 🛡️ Security & Compliance
- **PII Policy:** No real banking data. Use clearly marked "FAKE" prefixes in mock runbooks (e.g., `INCIDENT-001`).
- **Egress:** Strictly Local First. Even for this learning project, hardcode `http://localhost:11434` or env vars. Never point to external APIs.
