# 🤖 Agent Governance for python-sre-agent

This file governs how AI agents and developers interact with this repository.

## 🧠 Project Context
**Mission**: Build a local-first SRE Assistant that demonstrates "Tool Use" (Function Calling) + "RAG" using mock banking incident data.
**Target User**: Solo Dev / Portfolio Showcase.
**Infrastructure**: Runs locally against `ai-lab` server (RTX PRO 4000). Zero cloud egress allowed.

## 🛠️ Tech Stack & Rules
*   **Language**: Python 3.12+
*   **Linting/Formatting**: `ruff check src/` / `black src/`
*   **Testing**: `pytest tests/` (Must cover tool execution logic).
*   **Package Management**: Standard `requirements.txt`.

## ⚠️ Hardware Constraints
*   **RAM Limit**: Do not design vector stores requiring >16GB RAM. Use lightweight models for testing.
*   **GPU Limit**: Inference tasks must respect the 24GB VRAM limit on `ai-lab`.
*   **Storage**: Use in-memory ChromaDB instances for mock data to keep the repo "clean" (no massive local DB files in git).

## 📋 Process Gates (Phase 5: Development)
1.  **Tool Definition First**: Before writing agent logic, define the JSON schema for tools in `prompts.py`.
2.  **Mock Data Isolation**: All mock runbooks must live in `data/` and be loaded dynamically. No hardcoded text in the agent loop.
3.  **Error Handling**: Every tool function must catch exceptions and return a "Tool Error" string to the LLM, never crash the Python process.

## 🚫 Forbidden Actions
*   Do not commit local ChromaDB database files (`.chromadb/`, `chroma.sqlite3`).
*   Do not use public cloud embedding models (e.g., OpenAI API). Use local Ollama embeddings only.
