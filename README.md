# 🛠️ Python SRE Agent

A **Local-First AI Assistant** designed to simulate an Enterprise Site Reliability Engineer (SRE) / Production Support workflow. 

This project moves beyond basic LLM chatting by implementing a true **Tool-Using Agent Loop**. The model doesn't just generate text; it reasons over available tools, calls Python functions to query data, and synthesizes answers based on real-time system information.

---

## 🎯 Project Goals & Portfolio Value
Built for the `ai-lab` local infrastructure, this project demonstrates three critical engineering skills:

1.  **Tool Calling (Function Calling):** Implementing structured JSON schemas to let Ollama interact with Python code safely.
2.  **Retrieval-Augmented Generation (RAG):** Using an ephemeral **ChromaDB** instance to search a localized Knowledge Base of incident runbooks.
3.  **Enterprise Simulation:** Utilizing realistic, mocked banking/financial data (SWIFT transfers, PCI-DSS audits) to demonstrate how AI handles regulated, high-stakes operational tasks without ever touching the cloud.

## 🏗️ Architecture: The ReAct Loop
Unlike a standard chatbot that just predicts the next word, this agent follows a **Reason → Act → Observe** cycle:

1.  **User Input:** *"The SWIFT API is timing out, what's the fix?"*
2.  **LLM Analysis:** The model decides it lacks this information and generates a structured `tool_call` to search the runbooks.
3.  **Tool Execution:** Python intercepts the call, queries the in-memory vector database for relevant procedures, and gets back `"INCIDENT-001: Check VPN tunnel..."`.
4.  **Context Injection:** The tool result is fed back to the LLM.
5.  **Final Synthesis:** The model writes a final answer to the user grounded in the retrieved runbook.

## 🛠️ Tech Stack
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core logic and tool orchestration |
| **LLM Engine** | [Ollama](https://ollama.com/) | Local inference (e.g., `llama3`, `mistral`) |
| **Vector Store** | [ChromaDB](https://www.trychroma.com/) | In-memory RAG for runbook retrieval |
| **Linting/Testing**| Ruff / Pytest | Code quality and tool unit tests |

## 📚 Documentation
- **[PROJECT_GUIDE.md](./PROJECT_GUIDE.md)**: The architectural blueprint, learning resources, and design questions for this repo.
- **[AGENTS.md](./AGENTS.md)**: Governance rules, coding standards, and development gates.

---

> ⚠️ **Local-First Notice:** This project is designed to run entirely offline. No data ever leaves the `localhost` or internal `192.168.x.x` network.
