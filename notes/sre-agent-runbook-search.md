---
title: Python SRE Agent - Runbook Search Tool Implementation
subject: Python SRE Agent
section: Tool Implementation
phase: Phase 2 (Design) → Phase 3 (Implementation)
tags: [runbook-search, ChromaDB, vector-store, sre-tools, ollama-integration]
parent: Tool Calling Architecture & Design Patterns
source: Internal Design Notes
last_reviewed: 2026-10-13
next_review: 2026-10-20
---

## Summary
The Python SRE Agent implements a runbook search tool that guides agents toward incident response and troubleshooting workflows. The tool uses ChromaDB for semantic vector search and applies the "Golden Description" pattern to ensure the LLM only invokes it for domain-relevant queries (incident, error, SOP, alert).

This note documents the project-specific implementation details. For generic tool calling patterns, see [Tool Calling Architecture & Design Patterns](./tool-calling.md).

## Learning Objectives
- Design a semantic runbook search tool with clear trigger conditions
- Implement ChromaDB vector indexing for runbook retrieval
- Apply the Golden Description pattern to prevent spurious tool calls
- Structure tool errors for graceful agent retry logic

---

## Implementation: Runbook Search Tool

### Architecture Overview

**Data Store:**
- **Vector Database:** ChromaDB (in-memory mode for portability)
- **Content:** Mock runbooks prefixed with `INCIDENT-001`, `INCIDENT-002`, etc. (no real PII)
- **Indexing:** Semantic embeddings for fuzzy runbook matching (not keyword-only)

**Tool Flow:**
1. User input received by agent
2. Agent inspects available tools via `list_tools()`
3. If user mentions trigger keywords (`incident`, `error`, `alert`, `SOP`), agent invokes `search_runbooks(query)`
4. Function semantically searches ChromaDB for best-match runbook
5. Returns structured instructions to agent
6. Agent synthesizes response incorporating runbook guidance

### Answering the Core Question: How Strictly Do We Define Tool Descriptions?

**Question:** How strictly should tool descriptions constrain when an LLM invokes the tool?

**Answer:** **Very strictly.** Tool descriptions must explicitly list trigger keywords and negative constraints. Vague descriptions cause spurious invocations.

**Comparison:**

| Vague Description | Strict (Golden) Description |
| --- | --- |
| "Searches data" | "Search runbooks ONLY for incident, error, or SOP queries. Do NOT use for general knowledge." |
| Result: LLM calls for "Hello!" or "What's Kubernetes?" | Result: LLM skips tool for off-topic queries. |

**Test Cases to Validate Golden Description:**

| User Query | Should Call Tool? | Why? |
| --- | --- | --- |
| "Database connection timeout" | ✅ YES | Contains "timeout" (error keyword) |
| "How do I restart a service?" | ✅ YES | Troubleshooting intent |
| "We have an incident: service is down" | ✅ YES | Contains "incident" |
| "What is Kubernetes?" | ❌ NO | General knowledge; no error/incident keyword |
| "Hi, how are you?" | ❌ NO | Social greeting; not incident-related |
| "Tell me about SRE best practices" | ❌ NO | Learning/conceptual; not operational crisis |

**Implementation: Strict Golden Description**

The trigger keyword list prevents false positives while allowing legitimate use cases:

```python
def search_runbooks(query: str) -> str:
  """Search runbooks for troubleshooting steps and incident procedures.
  
  Use ONLY if user mentions: incident, error, failure, alert, SOP, 
  troubleshooting, workaround, root cause, or outage.
  
  Do NOT use for: general knowledge, conceptual questions, learning, 
  or non-incident contexts.
  
  Args:
    query: Search term extracted from user message
    
  Returns:
    Structured runbook instructions (steps, context, contact info) 
    or "No matching runbook found" if no relevant runbook exists
  """
```

**Why this description works:**
- ✅ Explicit positive trigger keywords (incident, error, alert, SOP, troubleshooting, workaround, root cause, outage)
- ✅ Explicit negative constraints (NOT for general knowledge, conceptual, learning, non-incident)
- ✅ Clear VERB + RESOURCE (Search runbooks)
- ✅ Describes return format (structured instructions or "not found")
- ✅ Forces agent to evaluate context before tool invocation (Golden Pattern)

### Tool Schema Requirements

**Ollama-Compatible Format:**
```json
{
  "type": "function",
  "function": {
    "name": "search_runbooks",
    "description": "Search runbooks for troubleshooting steps...",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Search term (e.g., 'database connection timeout')"
        }
      },
      "required": ["query"]
    }
  }
}
```

### Error Handling Strategy

Tools must catch exceptions and return structured strings to the LLM:

```python
def search_runbooks(query: str) -> str:
  try:
    results = chromadb_client.query(query, top_k=3)
    if not results:
      return "No matching runbook found for: '{query}'. Try searching for a different symptom."
    
    # Format results into structured response
    instructions = format_runbook_results(results)
    return instructions
    
  except VectorStoreError as e:
    return f"Runbook search temporarily unavailable: {str(e)}"
  except Exception as e:
    return f"Unexpected error searching runbooks: {str(e)}"
```

**Why structured errors matter:**
- LLM can understand and retry gracefully
- Agent loop continues without crashing
- User gets informative fallback response
- Enables Phase 5 logging for description refinement

---

## Sample Runbooks (Mock Data)

### INCIDENT-001: Database Connection Timeout

```
TITLE: Database Connection Timeout During Peak Load
KEYWORDS: timeout, database, connection, pool, peak load, latency
TRIGGER: User mentions timeout + database + slow queries

STEPS:
1. Check database connection pool status
2. Increase max_connections if < 80% utilization
3. Review slow query log for long-running queries
4. If still blocking, restart database replication slave

CONTACT: db-oncall@team.slack.com
ESCALATION: Platform team lead after 15 minutes
```

### INCIDENT-002: Service Unavailable (5xx Errors)

```
TITLE: Service Returns 5xx Errors
KEYWORDS: error, 500, 502, 503, service down, unavailable

STEPS:
1. Check service health endpoint: GET /health
2. Review recent logs for panic/crash messages
3. Verify dependent services (database, cache, API) are reachable
4. If unresponsive, trigger graceful restart
5. Monitor for recovery; alert on-call if not recovered in 2 min

CONTACT: platform-oncall@team.slack.com
ESCALATION: SRE manager after 5 minutes
```

---

## Phase 3 Implementation Checklist

- [ ] Create `src/tools/search_runbooks.py` with ChromaDB integration
- [ ] Implement `search_runbooks(query: str) -> str` function with error handling
- [ ] Create runbook mock data in `src/data/runbooks/` (5–10 sample incidents)
- [ ] Initialize ChromaDB collection with runbook embeddings
- [ ] Add tool to agent's tool registry with Golden Description
- [ ] Unit test tool invocation without running Ollama (mock LLM client)
- [ ] Integration test: Agent should NOT invoke runbook tool for "What is Kubernetes?"
- [ ] Integration test: Agent SHOULD invoke runbook tool for "Database connection timeout"

---

## Phase 5 Refinement (Monitoring & Iteration)

- [ ] Log all tool invocations (timestamp, query, matched runbook, success/failure)
- [ ] Analyze logs to identify:
  - False positive invocations (tool called unnecessarily)
  - False negative invocations (tool should have been called but wasn't)
  - Missed trigger keywords
- [ ] Refine Golden Description based on false positive/negative patterns
- [ ] Retrain ChromaDB embeddings if new incident types emerge

---

## Related Concepts
- **Semantic Search vs. Keyword Search:** ChromaDB embeddings match intent, not just keywords. "Database is slow" matches "Connection timeout" runbook.
- **Vector Drift:** As runbook content evolves, re-embed old runbooks to maintain relevance.
- **Cold Start Problem:** New incident types won't match until a runbook is added. Phase 5 monitoring surfaces gaps.
- **Tool Composition:** Future enhancement—chain runbook search with incident ticketing or alert creation tools.

---

## See Also
- [Tool Calling Architecture & Design Patterns](./tool-calling.md) — Generic tool calling patterns
- [AGENTS.md](../AGENTS.md) — Project governance and phase gates
- [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) — Full project structure
