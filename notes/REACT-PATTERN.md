---
title: ReAct Pattern for LLM Agents
subject: Agent Design, LLM Reasoning
section: Architecture Patterns
tags: [react, agent-loop, reasoning, tool-calling, llm, architecture]
source: ReAct Paper (Yao et al.), Ollama Function Calling, SRE Agent Phase 4 Design
last_reviewed: 2026-10-14
next_review: 2026-10-21
---

## Summary
**ReAct** = **Re**asoning + **Act**ing. A design pattern for agentic LLMs that interleaves language-based reasoning with tool invocations. The agent thinks through the problem, decides if a tool is needed, calls it, observes the result, and reasons about next steps—repeating until complete or max iterations reached. This reduces hallucinations and improves task completion vs. single-shot LLM calls.

---

## Learning Objectives
- Understand the ReAct loop: Thought → Action → Observation → Reasoning
- Distinguish ReAct from other patterns (Chain-of-Thought, Function Calling alone)
- Implement ReAct in Python with Ollama function calling
- Design for error recovery: tool failures, no matches, fallback strategies
- Apply to SRE agent context: runbook search, incident troubleshooting

---

## Key Points

### 1. The ReAct Loop (Core Cycle)

```
┌─────────────────────────────────────────┐
│ USER QUERY: "Database connection fails" │
└──────────────────┬──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   THOUGHT (Reason)   │  LLM generates internal reasoning
        │  "This is a database │  (What do I need to do?)
        │   connection issue.  │
        │   I should search    │
        │   for runbooks."     │
        └──────────────┬───────┘
                       │
                       ▼
        ┌──────────────────────┐
        │  ACTION (Tool Call)   │  LLM decides to invoke tool
        │ search_runbooks:     │  (Which tool? With what args?)
        │  query="connection   │
        │  pool timeout"       │
        │  max_results=3       │
        └──────────────┬───────┘
                       │
                       ▼
        ┌──────────────────────┐
        │  OBSERVATION (Result)│  Tool returns structured data
        │ [INCIDENT-001,       │  (What did the tool find?)
        │  INCIDENT-003,       │
        │  INCIDENT-006]       │
        └──────────────┬───────┘
                       │
                       ▼
        ┌──────────────────────┐
        │  REASONING (Update)  │  LLM interprets results
        │ "Good, I found 3     │  (What do these results mean?
        │ relevant runbooks.   │   Should I take another action?)
        │ Let me format and    │
        │ present them."       │
        └──────────────┬───────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
   [Need more info?]           [Complete?]
        │                             │
        ▼                             ▼
   (Loop)                      ┌──────────────┐
                               │ FINAL ANSWER │
                               │ Return       │
                               │ formatted    │
                               │ runbooks     │
                               └──────────────┘
```

**Key Elements:**
1. **Thought** — LLM's internal reasoning (not action yet)
2. **Action** — Tool name + structured arguments (from validated schema)
3. **Observation** — Tool result (success + data, or error message)
4. **Reasoning** — LLM interprets observation, decides next step

### 2. ReAct vs. Other Patterns

| Pattern | Approach | Hallucination Risk | Best For |
|---------|----------|-------------------|----------|
| **Single LLM Call** | Query LLM once, return answer | ⚠️ HIGH | Simple Q&A, summarization |
| **Chain-of-Thought** | LLM shows reasoning, no tools | ⚠️ MEDIUM | Multi-step reasoning without external data |
| **Function Calling** | LLM picks tool, no reasoning loop | ⚠️ MEDIUM | One-shot tool invocation |
| **ReAct (ours)** | Reason → Act → Observe → Loop | ✅ LOW | Complex tasks, tool chaining, incident resolution |

**Why ReAct is Better for SRE Agent:**
- User asks vague question: "Database is slow"
- ReAct: Thinks → searches runbooks → observes 3 matches → reasons about severity → returns context-aware runbooks
- Single call: Returns hallucinated steps (wrong! dangerous in SRE context)

---

## 3. ReAct Loop Implementation (Pseudocode)

```python
def react_agent(user_query: str, max_iterations: int = 5) -> str:
    """ReAct agent loop for SRE troubleshooting."""
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        
        # STEP 1: LLM Thinks & Decides Action
        response = llm.chat(
            model="qwen2.5-7b",
            messages=messages,
            tools=available_tools,  # Pass tool schemas
            temperature=0.3  # Lower temp = more focused reasoning
        )
        
        # Check if LLM decided to stop (no tool call)
        if response.stop_reason == "end_turn":
            return response.content  # Final answer
        
        # STEP 2: LLM Invokes Tool
        if response.stop_reason == "tool_use":
            tool_calls = response.tool_calls
            
            for tool_call in tool_calls:
                tool_name = tool_call.name
                tool_args = tool_call.arguments
                
                # STEP 3: Execute Tool → Observation
                try:
                    result = execute_tool(tool_name, tool_args)
                    observation = f"✅ Tool '{tool_name}' returned:\n{result}"
                except ToolError as e:
                    observation = f"❌ Tool '{tool_name}' failed: {e}"
                
                # STEP 4: Add Observation to Messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": observation
                })
        
        # Safety: Prevent infinite loops
        if iteration >= max_iterations:
            return f"⚠️ Max iterations ({max_iterations}) reached. Final response: {response.content}"
    
    return "Error: Loop exited unexpectedly"
```

---

## 4. Ollama Function Calling Integration (Phase 4 Specifics)

### Ollama's Direct Function Passing (Recommended)

**Ollama introspects Python functions directly** — no need for manual JSON schemas!

```python
from ollama import chat
from tools import search_runbooks

# PASS FUNCTION DIRECTLY - Ollama extracts docstring + params automatically
response = chat(
    model="qwen2.5-7b",
    messages=messages,
    tools=[search_runbooks],  # ← Just pass the function!
    temperature=0.3,
    stream=False
)

# Response structure (auto-parsed by Ollama):
# response.message = {
#     'role': 'assistant',
#     'content': '...',  # LLM's reasoning (Thought)
#     'tool_calls': [
#         {
#             'function': {
#                 'name': 'search_runbooks',  # ← From function name
#                 'arguments': {'query': '...', 'max_results': 5}  # ← Auto-parsed
#             }
#         }
#     ]
# }
```

**Why this is cleaner:**
- ✅ Single source of truth: your function definition
- ✅ Ollama reads docstring → auto description
- ✅ Ollama reads parameter types → auto schema
- ✅ No schema duplication, no drift
- ✅ Built-in argument parsing + validation

### Handling Tool Call Responses

```python
# Extract tool calls from response
if response.message.tool_calls:
    # LLM decided to use a tool
    for tool_call in response.message.tool_calls:
        func_name = tool_call.function.name
        args = tool_call.function.arguments  # ← Auto-parsed by Ollama
        
        # Call our tool with auto-parsed arguments
        try:
            result = search_runbooks(**args)
        except Exception as e:
            result = f"❌ Tool error: {type(e).__name__}: {str(e)}"
        
        # Add LLM's thought to messages
        messages.append({"role": "assistant", "content": response.message.content})
        
        # Add tool result using standard "tool" role
        messages.append({
            "role": "tool",
            "tool_name": func_name,
            "content": str(result)
        })
    
    # Continue loop: LLM re-evaluates with new information
else:
    # LLM didn't call tool → it's done reasoning
    return response.message.content
```

---

## 5. Error Handling Patterns for ReAct

### Pattern 1: Tool Validation Failure
```python
# User: "Show me runbooks with x (invalid query)"
# Phase 3 (tools.py) catches: ValidationError
# Returns: "❌ Invalid arguments: query must be 3-100 chars"
# Phase 4 (agent): Receives error string
#   → Adds to messages as observation
#   → LLM thinks: "Query validation failed, I need to rephrase"
#   → Loop continues with corrected query
```

### Pattern 2: No Results Found
```python
# User: "Find runbooks about Klingon starship failures"
# Phase 3 (tools.py) returns: "❌ No matching runbooks found"
# Phase 4 (agent): Observes empty result
#   → LLM reasons: "No results. Maybe I should try different keywords"
#   → OR: "No results. I should tell user we don't have a runbook"
#   → Decides based on context (max_iterations, task criticality)
```

### Pattern 3: Tool Execution Error
```python
# ChromaDB crashes, network down, etc.
# Try-except wraps tool call:
try:
    result = search_runbooks(query, max_results)
except Exception as e:
    result = f"❌ Tool error: {type(e).__name__}: {str(e)}"
    
# Add error as observation to messages
# LLM can then:
#   → Retry with different parameters
#   → Fall back to cached runbooks
#   → Tell user service is unavailable
```

### Pattern 4: Max Iterations Safeguard
```python
# Prevent infinite loops (LLM keeps calling tools endlessly)
max_iterations = 5

for iteration in range(max_iterations):
    # ... react loop ...
    if iteration == max_iterations - 1:
        return f"⚠️ Reached max iterations. Latest response: {response}"
```

---

## 6. Application to SRE Agent (Phase 4 Implementation)

### User Query Example
```
User: "I'm getting 'connection refused' errors on my database. What should I do?"
```

### ReAct Execution

**Iteration 1:**
- **Thought:** "User is reporting database connection errors. This is likely a connection pool exhaustion or network issue. I should search the runbook database."
- **Action:** `search_runbooks(query="connection refused database", max_results=3)`
- **Observation:** ✅ Found 3 runbooks: INCIDENT-001, INCIDENT-003, INCIDENT-006
- **Reasoning:** "Good, I found relevant runbooks on connection pool issues. Let me present these with severity and next steps."

**Iteration 2:**
- **Thought:** "The user needs clear, actionable steps. I should extract the relevant sections from INCIDENT-001."
- **Action:** Could call another tool (if we build one) for `get_runbook_details(id="INCIDENT-001")` OR format current results
- **Observation:** [Formatted runbook details + escalation contact]
- **Reasoning:** "Perfect, I have everything needed. Time to return final answer."

**Final Answer:**
```
I found 3 relevant runbooks for your issue:

**1. INCIDENT-001 — Database Connection Timeout During Peak Load (HIGH)**
Detection: Run 'SHOW STATUS LIKE Threads%' to check pool exhaustion
Remediation: [steps...]
Contact: db-oncall@team.slack.com
Escalate after 15min if not resolved

...
```

---

## 7. Design Decisions for Phase 4

### Question 1: Max Iterations
- **Answer:** 5 iterations max (prevents runaway loops)
- **Why:** Most SRE queries resolve in 1–2 iterations (search runbooks → format → done)
- **Fallback:** If max reached, return "best effort" answer + warn user

### Question 2: Temperature Setting
- **Answer:** temperature=0.3 (lower = more focused)
- **Why:** SRE context requires accuracy, not creativity. Lower temp = less hallucination
- **Contrast:** Creative writing would use temperature=0.7+

### Question 3: Tool Result Formatting
- **Answer:** Structured error strings + metadata in each result object
  - Errors: `"❌ [Error Type]: [Details]"`
  - Successes: `"✅ [Count] results: [id, title, severity, preview]"`
- **Why:** Consistent format helps LLM parse results reliably

### Question 4: Fallback When No Match
- **Answer:** 
  1. Try search with simplified keywords (LLM's decision)
  2. If still no match, return: "No runbooks found. Try keywords: [suggestions]"
  3. Offer: "Would you like general troubleshooting tips?"
- **Why:** User still gets help even with novel issue

---

## 8. Implementation: `src/agent.py` Structure (Phase 4 Deliverable)

**Key difference from pseudocode above:** We pass functions DIRECTLY to Ollama, not JSON schemas!

```python
"""src/agent.py — ReAct loop for SRE agent using Ollama function calling."""

from ollama import chat
from tools import search_runbooks  # ← Just the function, no schema needed!
from db import seed_runbooks

SYSTEM_PROMPT = """You are an SRE troubleshooting assistant.
Help users resolve incidents by searching runbooks and providing clear, 
actionable steps.

When a user reports an issue:
1. THINK: What is the core problem?
2. ACT: Search runbooks for relevant procedures
3. OBSERVE: What runbooks matched?
4. REASON: How should I present this?

Focus on clarity, safety, and escalation paths."""

def react_agent(user_query: str, max_iterations: int = 5, verbose: bool = False) -> str:
    """ReAct loop for SRE troubleshooting."""
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        
        if verbose:
            print(f"Iteration {iteration}/{max_iterations}")
        
        # Pass function DIRECTLY - Ollama introspects docstring + params
        response = chat(
            model="qwen2.5-7b",
            messages=messages,
            tools=[search_runbooks],  # ← No JSON schema needed!
            temperature=0.3,
            stream=False
        )
        
        # Check if LLM decided to use tools
        if not response.message.tool_calls:
            # No tool call = LLM is done reasoning
            return response.message.content
        
        # Execute tools
        for tool_call in response.message.tool_calls:
            func_name = tool_call.function.name
            args = tool_call.function.arguments  # ← Auto-parsed!
            
            # Execute tool
            try:
                result = search_runbooks(**args)
            except Exception as e:
                result = f"❌ Tool error: {type(e).__name__}: {str(e)}"
            
            # Add to message history using standard Ollama format
            messages.append({"role": "assistant", "content": response.message.content})
            messages.append({
                "role": "tool",
                "tool_name": func_name,
                "content": str(result)
            })
    
    # Max iterations reached
    return f"⚠️ Max iterations ({max_iterations}) reached. Last response: {response.message.content}"

if __name__ == "__main__":
    query = "Database connection pool exhausted, 500 errors"
    answer = react_agent(query, verbose=True)
    print(answer)
```

**What's different from traditional function calling:**
- ✅ NO hardcoded JSON schemas
- ✅ NO schema duplication or drift
- ✅ Ollama reads your function's docstring for description
- ✅ Ollama reads parameter types + annotations for schema
- ✅ Arguments auto-parsed by Ollama (type-safe)
- ✅ Cleaner message format with `"role": "tool"`
- ✅ Much easier to add new tools (just define function + docstring)

---

## 9. Common Pitfalls & How to Avoid

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **No max iterations** | Infinite loops, wasted tokens | Set max_iterations=5 |
| **Poor tool descriptions** | LLM misuses tools, hallucinations | Use "Golden Description" (see tool-calling.md) |
| **Not handling tool errors** | Agent crashes or hangs | Wrap in try-except, return error string |
| **High temperature** | Unpredictable tool calls | Use temperature=0.3 for SRE tasks |
| **Tool results too verbose** | LLM gets lost, wastes tokens | Limit previews to 200 chars, include only essential metadata |
| **No observation feedback loop** | LLM doesn't learn from results | Always add tool result back to messages |

---

## 10. Testing ReAct (Phase 4 QA)

### Unit Tests: Iterate independently
```python
# test_agent.py
def test_react_loop_stops_on_no_tools():
    """Agent should stop when LLM doesn't call tools."""
    query = "What is an SRE?"  # Doesn't require search
    result = react_agent(query)
    assert len(result) > 0
    assert "❌" not in result

def test_react_loop_handles_validation_error():
    """Agent should handle tool validation failures gracefully."""
    query = "Find runbooks for ab"  # Too short, triggers validation error
    result = react_agent(query)
    assert "Invalid arguments" in result  # Should retry or fail gracefully

def test_react_loop_max_iterations_safeguard():
    """Agent should stop at max_iterations."""
    result = react_agent("query", max_iterations=1)
    assert "Max iterations" in result or len(result) > 0
```

### Integration Tests: End-to-end
```python
def test_react_e2e_database_timeout():
    """Full flow: database issue query → runbook search → formatted answer."""
    query = "Database connection timeout errors"
    result = react_agent(query)
    
    # Should contain runbook info
    assert "INCIDENT-" in result
    assert "Severity:" in result
    assert "Contact:" in result
```

---

## 11. Next Steps (Phase 4 Execution)

1. ✅ Phases 2–3 complete (db + tools ready)
2. **Build src/agent.py** with full ReAct loop (use pseudocode above)
3. **Integrate with Ollama** (model: qwen2.5-7b or qwen2.5-1.5b)
4. **Test end-to-end:** `python src/agent.py "query"`
5. **Add retry logic** for failed tool calls
6. **Benchmark:** iterations, tokens, latency
7. **Phase 5:** Wrap in test suite + API layer

---

## References

- **ReAct Paper:** [Reasoning + Acting in Language Models](https://arxiv.org/abs/2210.03629) (Yao et al.)
- **Ollama Function Calling:** https://github.com/ollama/ollama/blob/main/docs/api.md#model-with-function-calling
- **Tool Calling Best Practices:** See `tool-calling.md` in this repo
- **SRE Agent Design:** See `AGENTS.md` in this repo
