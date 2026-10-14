---
title: Preventing LLM Hallucinations in Tool Calling
subject: Agent Safety & Input Validation
date: 2026-10-13
tags: [hallucinations, pydantic, tool-calling, validation, error-handling]
---

## 🚨 **What Are LLM Hallucinations in Tool Calling?**

When your LLM calls a tool, it generates **structured JSON arguments**. But the LLM can:
- ✗ Pass empty strings (`query=""`)
- ✗ Pass unexpected fields (`extra_param="value"`)
- ✗ Pass wrong types (`query=123` instead of `query="string"`)
- ✗ Violate constraints (e.g., `max_retries=-5`)

**Hallucination in this context:** The LLM confidently generates invalid data that will crash your tool or produce meaningless results.

---

## 🛡️ **Defense Layers**

### Layer 1: Tool Description (Prevention)
**Golden Description Pattern** — explicitly constrain in tool schema:

```python
{
    "type": "function",
    "function": {
        "name": "search_runbooks",
        "description": "Search runbooks for incident troubleshooting. "
                      "Use ONLY for incident, error, failure, SOP queries. "
                      "Do NOT use for general knowledge or learning. "
                      "Query must be 3-100 characters.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords (e.g., 'database timeout', 'memory leak')"
                }
            },
            "required": ["query"]
        }
    }
}
```

✅ **Why this helps:** LLM sees constraints in the description and is more likely to respect them.  
❌ **Why it's not enough:** LLM still hallucinates ~5-15% of the time.

---

### Layer 2: Pydantic Validation (Detection & Rejection)

**Pydantic enforces type safety and custom constraints at runtime:**

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class SearchRunbooksInput(BaseModel):
    """Validate tool arguments before execution."""
    
    query: str = Field(
        ...,  # Required
        min_length=3,
        max_length=100,
        description="Search keywords for runbook lookup"
    )
    
    max_results: Optional[int] = Field(
        default=5,
        ge=1,  # Greater than or equal to 1
        le=20,
        description="Max runbooks to return (1-20)"
    )
    
    @field_validator('query')
    @classmethod
    def query_not_empty_or_whitespace(cls, v: str) -> str:
        """Reject empty or whitespace-only queries."""
        if not v.strip():
            raise ValueError("query cannot be empty or whitespace-only")
        return v.strip()

# Usage in your agent loop:
try:
    tool_args = response.message.tool_calls[0].function.arguments
    validated_args = SearchRunbooksInput(**tool_args)
    result = search_runbooks(validated_args.query, validated_args.max_results)
except ValueError as e:
    # LLM passed invalid data
    return f"Tool validation failed: {e}. Please try again with valid parameters."
```

✅ **What this catches:**
- Empty queries (`query=""` → ValueError)
- Wrong types (`max_results="five"` → TypeError)
- Out-of-range values (`max_results=100` → ValueError)
- Extra fields (silently ignored or error, depending on config)

---

### Layer 3: Tool Wrapper Logic (Recovery)

**Graceful degradation — don't crash, return structured error:**

```python
def search_runbooks_safe(query: str, max_results: int = 5) -> str:
    """
    Wrapper around ChromaDB search with error handling.
    
    Args:
        query: Search string (validated by Pydantic)
        max_results: Max results to return (default 5)
    
    Returns:
        Either formatted runbook results or structured error message
    """
    try:
        # Validate inputs (defensive programming)
        if not query or len(query) < 3:
            return "⚠️ Error: Query must be at least 3 characters"
        
        if max_results < 1 or max_results > 20:
            return "⚠️ Error: max_results must be between 1 and 20"
        
        # Query ChromaDB
        results = chroma_client.collection.query(
            query_texts=[query],
            n_results=max_results
        )
        
        # No results found
        if not results or not results['documents']:
            return f"❌ No matching runbook found for: '{query}'"
        
        # Format and return
        formatted = "\n".join([
            f"📋 {doc['title']}\nSteps: {doc['steps']}\nContact: {doc['contact']}"
            for doc in results['documents']
        ])
        return formatted
    
    except Exception as e:
        # Catch ChromaDB failures, network errors, etc.
        return f"⚠️ Runbook search temporarily unavailable: {str(e)}"
```

✅ **Why this pattern works:**
- Returns **string error** (not exception) to LLM
- LLM can read the error and decide to retry or admit failure
- Agent loop stays stable (no crash)

---

## 📋 **Hallucination Prevention Checklist for Tool Calling**

### Before Implementation
- [ ] Define tool description with explicit constraints (in schema)
- [ ] Document valid/invalid input examples in docstring
- [ ] Identify required vs optional fields

### During Implementation
- [ ] Create Pydantic model for each tool's arguments
- [ ] Add Field constraints (`min_length`, `max_length`, `ge`, `le`)
- [ ] Implement custom validators for complex logic
- [ ] Wrap tool in error handler (return string, not exception)

### Testing
- [ ] Unit test: valid arguments → correct result
- [ ] Unit test: empty query → validation error
- [ ] Unit test: wrong type → validation error
- [ ] Unit test: out-of-range value → validation error
- [ ] Integration test: LLM hallucinates bad args → graceful error returned to LLM

---

## 🧪 **Example: Full Tool Pipeline with Validation**

```python
from pydantic import BaseModel, Field
import json

# 1. Define validation schema
class SearchRunbooksInput(BaseModel):
    query: str = Field(min_length=3, max_length=100)
    max_results: int = Field(default=5, ge=1, le=20)

# 2. Define tool schema (passed to Ollama)
SEARCH_RUNBOOKS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_runbooks",
        "description": "Search SRE runbooks. Use ONLY for incident/error queries.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keywords"},
                "max_results": {"type": "integer", "description": "Max results (1-20)"}
            },
            "required": ["query"]
        }
    }
}

# 3. Call LLM with tool
response = ollama.chat(
    model="qwen2.5:7b",
    messages=[
        {"role": "user", "content": "Database is timing out"}
    ],
    tools=[SEARCH_RUNBOOKS_TOOL]
)

# 4. Validate and execute
if response.message.tool_calls:
    for tool_call in response.message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = tool_call.function.arguments
        
        if tool_name == "search_runbooks":
            try:
                # Validate
                validated = SearchRunbooksInput(**tool_args)
                # Execute
                result = search_runbooks_safe(
                    query=validated.query,
                    max_results=validated.max_results
                )
            except ValueError as e:
                result = f"Invalid arguments: {e}"
        
        # Inject result back to LLM
        messages.append({
            "role": "assistant",
            "content": response.message.content,
            "tool_calls": [tool_call]
        })
        messages.append({
            "role": "tool",
            "content": result,
            "name": tool_name
        })

# 5. Get final response
final_response = ollama.chat(model="qwen2.5:7b", messages=messages)
```

---

## 🎯 **Real-World Scenarios**

### Scenario 1: Empty Query (Hallucination)
```
LLM generates: {"query": "", "max_results": 5}
Pydantic catches: ValueError (min_length=3 violated)
Tool returns: "❌ No matching runbook found for: ''"
LLM observes: Error, tries different query
```

### Scenario 2: Invalid Max Results
```
LLM generates: {"query": "timeout", "max_results": 1000}
Pydantic catches: ValueError (le=20 violated)
Tool returns: "⚠️ Error: max_results must be between 1 and 20"
LLM observes: Error, retries with max_results=5
```

### Scenario 3: Unexpected Field
```
LLM generates: {"query": "timeout", "ignore_cache": true}
Pydantic config: extra="ignore" (silently drop unknown fields)
Tool receives: query="timeout", max_results=5 (default)
Result: Correct runbook returned despite hallucinated extra field
```

---

## 📚 **References**

- **Pydantic Docs:** https://docs.pydantic.dev/latest/
- **Field Constraints:** https://docs.pydantic.dev/latest/concepts/fields/
- **Custom Validators:** https://docs.pydantic.dev/latest/concepts/validators/
- **Error Handling Best Practice:** Return structured error strings to LLM (not exceptions)

---

## ✅ **Checklist for Your SRE Agent**

- [ ] Pydantic model defined for `search_runbooks` arguments
- [ ] Field constraints match tool description
- [ ] Tool wrapper catches all exceptions
- [ ] Integration tests cover hallucination scenarios (empty, invalid types, out-of-range)
- [ ] Error messages are clear and actionable for LLM
- [ ] Max retries counter prevents infinite loops (from PROJECT_GUIDE Q3)

