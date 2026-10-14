---
title: Tool Calling Architecture & Design Patterns
subject: Agent Design
section: Core Concepts
tags: [tool-calling, function-calling, architecture, embedded-calling, agent-design]
source: Merge.dev, Ollama Documentation, Internal Research
last_reviewed: 2026-10-13
next_review: 2026-10-20
---

## Summary
Tool calling enables LLMs to invoke functions, APIs, and external resources during inference. Traditional function-calling approaches trigger hallucinations and spurious tool invocations. Embedded tool calling mitigates this risk by embedding tool context into the model's reasoning loop. Tool descriptions are the critical design component—they determine whether agents invoke the correct tool. The "Golden Description" pattern enforces semantic constraints to reduce hallucinations.

## Learning Objectives
- Understand traditional vs. embedded tool calling and their tradeoffs
- Design descriptions that guide agent tool selection
- Apply VERB + RESOURCE pattern and semantic constraints
- Separate tool schema (HOW) from descriptions (WHEN/WHY)

---

## Key Points

### 1. Embedded Tool Calling vs. Traditional Tool Calling
- **Problem:** Traditional tool calling causes hallucinations—models invoke tools unnecessarily or incorrectly.
- **Solution:** Embedded tool calling (supported by Ollama 2024+) reduces hallucinations by embedding tool context directly in the model's reasoning loop.
- **Why it matters:** Prevents wasted API calls, improves agent reliability, reduces token overhead.
- **Evidence:** [YouTube: Embedded Tool Calling](https://www.youtube.com/watch?v=h8gMhXYAv1k)

### 2. Tool Description Best Practices
**Format:** 1–2 sentence breakdown using **VERB + RESOURCE** pattern  
**Why it matters:** Agents inspect descriptions via `list_tools()` or `list_resources()` at runtime—unclear descriptions cause misuse.

**Best Practices** (via [Merge Agent Handler](https://www.merge.dev/merge-agent-handler)):
1. **Front-load critical info** – AI agents may truncate long descriptions. Put intent + trigger conditions first.
2. **Test with sample prompts** – Validate descriptions against 5–10 realistic user queries before deployment.
3. **Schema ≠ Description** – Authentication, pagination, filtering, error codes belong in JSON schema. Description focuses on WHEN to use and WHY.
4. **Negative constraints matter** – Explicitly state when NOT to use the tool (e.g., "Do NOT use for general knowledge questions").
5. **Golden Description Pattern** – Write 1–2 sentences with explicit positive + negative trigger conditions. Example: "Search knowledge base for troubleshooting. Use ONLY for incidents, errors, or SOP queries. Do NOT use for general knowledge."

**Reference:** [MCP Tool Description Best Practices](https://www.merge.dev/blog/mcp-tool-description)

**Example – BAD Description:**
```
Authenticate with API key, fetch paginated results, filter by status, return JSON
```
→ Too operational; mixes schema concerns with intent; no trigger conditions.

**Example – GOOD Description (Golden Pattern):**
```
Search knowledge base by keyword. Use only for troubleshooting, error diagnosis, or incident queries. Do NOT use for general knowledge.
```
→ Clear VERB (Search), clear RESOURCE (knowledge base), explicit positive + negative constraints.

### 3. Function Calling Implementation Example (Ollama)
```python
from ollama import chat

def get_temperature(city: str) -> str:
  """Get the current temperature for a city
  
  Args:
    city: The name of the city

  Returns:
    The current temperature for the city
  """
  temperatures = {
    'New York': '22°C',
    'London': '15°C',
  }
  return temperatures.get(city, 'Unknown')

available_functions = {
  'get_temperature': get_temperature,
}
# Ollama handles function routing automatically via type hints + docstrings
response = chat(model='qwen3', messages=messages, tools=available_functions.values(), think=True)
```

---

## Design Pattern: Tool Discovery & Agent Selection

When an agent receives input, it inspects available tools by calling `list_tools()` or `list_resources()`. The agent reads all tool descriptions and selects the appropriate one based on:
1. User intent (inferred from input)
2. Tool description (VERB + RESOURCE + constraints)
3. Tool schema (parameters, error codes)

**Critical Design Implication:** Tool descriptions must be self-contained and unambiguous. Poor descriptions cause:
- Agent calling wrong tool → wasted token overhead
- Agent refusing correct tool → incomplete responses  
- Spurious tool invocations → reduced reliability
- Hallucinations → tool misuse

**Solution:** Enforce trigger conditions explicitly in descriptions. Example trigger conditions:
- Positive: "Use for troubleshooting, error diagnosis, incident analysis"
- Negative: "Do NOT use for general knowledge, learning, or conceptual questions"

---

## Tool Error Handling & Graceful Degradation

Tool invocations may fail (network timeout, VectorStore error, validation failure). Proper error handling:

1. **Catch exceptions** in tool implementation—never crash the agent loop
2. **Return structured error strings** to the LLM (e.g., "Tool failed: reason here")
3. **Allow agent to retry or work around** the failure gracefully
4. **Log failures** for post-execution analysis and description refinement

---

## Related Concepts
- **Tool Discovery via list_tools():** Agents inspect available tools at runtime; descriptions are the primary selection signal
- **Schema vs. Description Separation:** JSON schema defines HOW (parameters, types, errors); description defines WHEN/WHY (trigger conditions, constraints)
- **Prompt Injection in Tool Descriptions:** Adversarial users can exploit vague descriptions—be explicit with constraints
- **Tool Composition:** Multiple tools can chain via agent loop (e.g., search → validate → alert)
- **Graceful Degradation:** Always allow agent to continue if a tool fails—no crashes or silent failures
- **Semantic Constraint Enforcement:** Description is the mechanism for encoding "use this tool only when..." logic
- **Golden Description Pattern:** Explicit positive + negative trigger conditions in docstring to prevent hallucination

---

## External Resources
- [Merge.dev: MCP Tool Description Best Practices](https://www.merge.dev/blog/mcp-tool-description)
- [Merge.dev: Merge Agent Handler](https://www.merge.dev/merge-agent-handler)
- [YouTube: Embedded Tool Calling](https://www.youtube.com/watch?v=h8gMhXYAv1k)
- Ollama Documentation: Function Calling (local embedding-based tool routing)

---

## Project Application
See [Python SRE Agent: Runbook Search Tool Implementation](./sre-agent-runbook-search.md) for a concrete implementation of these patterns using ChromaDB vector search and the Ollama inference engine. 

