---
title: Reference - LLM Chatbot Learnings & Patterns
subject: Python SRE Agent
section: Cross-Project Reference
tags: [ollama, streaming, architecture, dependency-management, python-compatibility]
source: https://github.com/msjackiebrown/python-llm-powered-chatbot
related: [tool-calling.md, sre-agent-runbook-search.md]
last_reviewed: 2026-10-13
next_review: 2026-10-27
---

## Summary
The [python-llm-powered-chatbot](https://github.com/msjackiebrown/python-llm-powered-chatbot) project demonstrates practical patterns for building Ollama-based applications. Key insights on streaming architecture, conversation history management, dependency stability, and runtime compatibility are directly applicable to the Python SRE Agent.

## Applicable Patterns

### 1. Streaming Architecture with Separate Channels
**Pattern:** Event-driven streaming with separate thinking/content channels
```python
# Ollama returns streaming response with two channels:
# - thinking: Model's internal reasoning process
# - content: Final response text
# Each channel streams independently
```

**Application to SRE Agent:**
- Agent's ReAct loop can display thinking process in real-time
- Tool invocation steps stream as they execute
- Final synthesized response streams to user
- Consider adding visualization layer (progress bar for tool calls)

**Reference:** chatbot.py streaming implementation

---

### 2. Conversation History as Agent Memory
**Pattern:** Maintain full context by appending each turn (user + assistant response)

**Chatbot Example:**
```python
messages = []  # Initialize empty history

# Each turn:
messages.append({"role": "user", "content": user_input})
response = chat(model, messages=messages)  # LLM sees full history
messages.append({"role": "assistant", "content": response})
```

**Application to SRE Agent:**
- Store conversation turns: `[user_query, agent_thought, tool_call, tool_result, agent_response]`
- Pass full history to LLM on each ReAct loop iteration
- Helps agent avoid repeating tool calls or contradicting earlier reasoning
- ChromaDB vector results should be injected as `<tool_response>` tags in message history

**Why it matters:**
- Without history, agent may hallucinate or repeat mistakes
- With history, agent can learn from previous tool failures
- Enables Phase 5 audit logging (trace complete decision path)

---

### 3. Python Version Compatibility & Startup Checks
**Problem:** Ollama SDK incompatible with Python 3.14+; pydantic_core version drift

**Chatbot Solution:**
- Document supported versions: **Python 3.11, 3.12, 3.13**
- Add startup check with friendly error message (not raw traceback)
- Update requirements.txt with explicit version constraints

**Application to SRE Agent:**
```python
import sys

def check_python_version():
    version = sys.version_info
    supported = (3, 11), (3, 12), (3, 13)
    if (version.major, version.minor) not in supported:
        print(f"Error: Python {version.major}.{version.minor} not supported.")
        print(f"Please use Python 3.11, 3.12, or 3.13")
        sys.exit(1)

if __name__ == "__main__":
    check_python_version()
    # ... continue with agent setup
```

**Action:** Add to `src/agent.py` main()

---

### 4. Runtime Health Checks (Ollama Service + Dependencies)
**Pattern:** Verify Ollama daemon and model availability before starting

**Chatbot Commands:**
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Or use Ollama CLI
ollama list
```

**Application to SRE Agent:**

```python
import requests

def check_ollama_service():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code != 200:
            raise ConnectionError("Ollama service not responding")
        print("✓ Ollama service is running")
    except Exception as e:
        print(f"✗ Ollama service check failed: {e}")
        print("  Start Ollama: ollama serve")
        sys.exit(1)

def check_model_available(model_name):
    response = requests.get("http://localhost:11434/api/tags")
    models = [m['name'] for m in response.json().get('models', [])]
    if model_name not in models:
        print(f"✗ Model '{model_name}' not found")
        print(f"  Pull model: ollama pull {model_name}")
        sys.exit(1)
    print(f"✓ Model '{model_name}' available")
```

**Add to SRE Agent Phase 3:**
- [ ] Check Ollama service is reachable
- [ ] Check requested model is pulled
- [ ] Check ChromaDB can initialize
- [ ] Print friendly setup guide if any check fails

---

### 5. System Prompt as Agent Personality Configuration
**Pattern:** Define agent role and constraints in system prompt at startup

**Chatbot Example:**
```python
SYSTEM_PROMPT = (
    "You are a helpful AI assistant. "
    "Answer questions accurately and concisely."
)
```

**Application to SRE Agent:**
```python
SRE_AGENT_PROMPT = (
    "You are an SRE Agent specializing in incident response and troubleshooting. "
    "Your role is to search runbooks, diagnose issues, and guide operators toward resolution. "
    "Always acknowledge when you cannot find a solution and suggest escalation. "
    "Never make up runbook content—only use information from the search_runbooks tool."
)
```

**Why it matters:**
- Sets agent's "personality" and constraints
- Reduces hallucination by defining scope upfront
- Makes agent behavior predictable and auditable
- Enables Phase 5 A/B testing different prompt variants

---

### 6. Dependency Maintenance & Version Drift
**Challenge:** Ollama SDK, pydantic, and Python versions can drift compatibility quickly

**Chatbot's Approach:**
- Maintain dated notes on compatibility issues (`2026-02-23.md`)
- Document when dependencies were last verified
- Add Python version guardrails
- Plan regular testing schedule

**Application to SRE Agent:**
- Document Python version constraint: **3.11-3.13**
- Record Ollama SDK version used: `ollama>=0.1.0,<1.0.0`
- Pin ChromaDB version for stability
- Add note in README: "Last dependency check: 2026-10-13"
- Phase 5: Schedule monthly compatibility verification

**Example requirements.txt:**
```
ollama>=0.1.0,<1.0.0  # Tested with 0.3.0
chromadb>=0.5.0,<1.0.0  # Tested with 0.5.1
pydantic>=2.0.0,<3.0.0  # Ollama SDK dependency
# Python 3.11, 3.12, or 3.13 required (pydantic_core incompatible with 3.14+)
```

---

## Startup Checklist for SRE Agent (Phase 3)

```python
def startup_checks():
    """Verify all dependencies before starting agent loop."""
    checks = [
        ("Python Version", check_python_version),
        ("Ollama Service", check_ollama_service),
        ("Model Available", lambda: check_model_available("qwen3")),
        ("ChromaDB Init", check_chromadb_connectivity),
        ("Runbook Data", check_runbook_seeds),
    ]
    
    for check_name, check_fn in checks:
        try:
            check_fn()
            print(f"✓ {check_name}")
        except Exception as e:
            print(f"✗ {check_name}: {e}")
            return False
    return True

if __name__ == "__main__":
    if not startup_checks():
        print("\n⚠️  Setup incomplete. See troubleshooting guide: README.md")
        sys.exit(1)
    start_agent_loop()
```

---

## Known Compatibility Issues

| Issue | Workaround | Status |
| --- | --- | --- |
| Python 3.14+ incompatible with pydantic_core | Use Python 3.11-3.13 | Verified 2026-10-13 |
| Ollama daemon not running | `ollama serve` in separate terminal | N/A |
| Model not pulled | `ollama pull qwen3` | N/A |
| ChromaDB in-memory overflow | Implement pagination/cleanup | TBD Phase 5 |

---

## Cross-Project References

- **Chatbot Project:** https://github.com/msjackiebrown/python-llm-powered-chatbot
- **Chatbot Dependency Notes:** https://github.com/msjackiebrown/python-llm-powered-chatbot/blob/main/docs/LLM%20AI%20ChatBot/2026-02-23.md
- **Chatbot README:** https://github.com/msjackiebrown/python-llm-powered-chatbot/blob/main/README.md

---

## Next Steps (Recommended Phase 3 Tasks)

- [ ] Implement startup checks in `src/agent.py` main()
- [ ] Copy Python version guardrails pattern
- [ ] Add Ollama service health check
- [ ] Document Python 3.11-3.13 requirement in README
- [ ] Create dated troubleshooting notes file (e.g., `docs/2026-10-13-setup.md`)
- [ ] Add "Known Issues" section to README
- [ ] Test on multiple Python versions (3.11, 3.12, 3.13)
