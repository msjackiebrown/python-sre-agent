---
title: Pydantic for Beginners - Tool Calling Validation
subject: Entry-Level Pydantic Tutorial for SRE Agent
date: 2026-10-14
tags: [pydantic, validation, basemodel, field, tutorial, beginner]
source: https://pydantic.dev/docs/validation/latest/get-started/
---

## 🚀 **What is Pydantic?**

Pydantic is a Python library that **validates data and enforces type safety**. Think of it as a "data bouncer" — it checks if data coming in is valid before your code tries to use it.

**Why do you need it for tool calling?**
- The LLM generates tool arguments as JSON
- LLM can hallucinate bad data (empty strings, wrong types, invalid values)
- Pydantic validates the data **before** it reaches your tool
- If data is invalid, Pydantic raises an error with clear messages

**For your SRE agent:**
- LLM → generates JSON → Pydantic validates → Tool executes safely → No crashes

---

## 📦 **Installation**

```bash
pip install pydantic
```

That's it! No configuration needed.

---

## 🏗️ **Core Concept: BaseModel**

Think of `BaseModel` like a Python class with built-in validation.

### Basic Example

```python
from pydantic import BaseModel

# Define a model (like a contract for data)
class User(BaseModel):
    name: str           # Must be a string
    age: int            # Must be an integer
    email: str          # Must be a string

# Valid data → works!
user = User(name="Alice", age=30, email="alice@example.com")
print(user.name)  # → "Alice"

# Invalid data → error!
try:
    user = User(name="Bob", age="thirty", email="bob@example.com")
except Exception as e:
    print(f"Error: {e}")  # → age is not a valid integer
```

**Key takeaway:** Type hints (`name: str`) are now enforced at runtime, not just comments.

---

## 🎯 **Your First Tool: Validation Model**

This is what you'll use for the `search_runbooks` tool:

```python
from pydantic import BaseModel, Field
from typing import Optional

class SearchRunbooksInput(BaseModel):
    """Model for validating search_runbooks arguments."""
    
    query: str                      # Required field (no default)
    max_results: Optional[int] = 5  # Optional field (default: 5)

# LLM generates this JSON
llm_generated_json = {
    "query": "database timeout",
    "max_results": 10
}

# Validate it
try:
    validated = SearchRunbooksInput(**llm_generated_json)
    print(validated.query)        # → "database timeout"
    print(validated.max_results)  # → 10
except Exception as e:
    print(f"Validation failed: {e}")
```

---

## 🛡️ **Adding Constraints with Field()**

`Field()` lets you add rules:

```python
from pydantic import BaseModel, Field

class SearchRunbooksInput(BaseModel):
    # Query must be 3-100 characters
    query: str = Field(
        ...,                    # ... means "required"
        min_length=3,           # At least 3 characters
        max_length=100,         # At most 100 characters
        description="Search keywords"
    )
    
    # Max results must be between 1-20
    max_results: int = Field(
        default=5,              # Default value if not provided
        ge=1,                   # Greater than or equal to 1
        le=20,                  # Less than or equal to 20
        description="Number of results (1-20)"
    )

# Valid
valid = SearchRunbooksInput(query="timeout", max_results=10)  # ✅ Works

# Invalid: query too short
try:
    invalid = SearchRunbooksInput(query="db")  # Only 2 characters
except Exception as e:
    print(f"Error: {e}")  # ✅ Caught!

# Invalid: max_results out of range
try:
    invalid = SearchRunbooksInput(query="timeout", max_results=100)
except Exception as e:
    print(f"Error: {e}")  # ✅ Caught!
```

---

## 🔍 **Common Field Constraints**

| Constraint | Example | Meaning |
|-----------|---------|---------|
| `min_length` | `min_length=3` | Minimum string length |
| `max_length` | `max_length=100` | Maximum string length |
| `ge` (≥) | `ge=1` | Greater than or equal to |
| `le` (≤) | `le=20` | Less than or equal to |
| `gt` (>) | `gt=0` | Greater than |
| `lt` (<) | `lt=100` | Less than |
| `pattern` | `pattern=r"^[a-z]+$"` | Regex validation |
| `default` | `default=5` | Default value if not provided |
| `...` | `...` (required) | Field is required |

---

## ✅ **Handling Errors: Try/Except**

When Pydantic validation fails, it raises `ValidationError`:

```python
from pydantic import BaseModel, ValidationError

class SearchRunbooksInput(BaseModel):
    query: str
    max_results: int

# Bad input
try:
    input_data = {"query": ""}  # Empty query, missing max_results
    validated = SearchRunbooksInput(**input_data)
except ValidationError as e:
    # e.errors() gives detailed error info
    print(e.errors())
    # Output:
    # [
    #     {
    #         'type': 'string_too_short',
    #         'loc': ('query',),
    #         'msg': 'String should have at least 1 character',
    #         'input': '',
    #     },
    #     {
    #         'type': 'missing',
    #         'loc': ('max_results',),
    #         'msg': 'Field required',
    #         'input': {},
    #     }
    # ]
```

**In your agent code:**

```python
try:
    validated_args = SearchRunbooksInput(**tool_args)
    result = search_runbooks(validated_args.query, validated_args.max_results)
except ValidationError as e:
    result = f"❌ Validation failed: {e.errors()[0]['msg']}"
    # Return error string to LLM instead of crashing
```

---

## 🧩 **Converting to Dict/JSON**

Sometimes you need to convert validated data back to a dictionary:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

user = User(name="Alice", age=30)

# Convert to dictionary
user_dict = user.model_dump()
print(user_dict)  # → {'name': 'Alice', 'age': 30}

# Convert to JSON string
user_json = user.model_dump_json()
print(user_json)  # → '{"name":"Alice","age":30}'
```

---

## 🎓 **Practical Example: For Your SRE Agent**

Here's the full pattern for your tool:

```python
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

# 1. Define validation model
class SearchRunbooksInput(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Search keywords (e.g., 'database timeout')"
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Max runbooks to return (1-20)"
    )

# 2. Define tool function
def search_runbooks_safe(query: str, max_results: int = 5) -> str:
    """Safe wrapper with validation."""
    try:
        # Validate inputs (defensive)
        if not query or len(query) < 3:
            return "❌ Query must be at least 3 characters"
        if max_results < 1 or max_results > 20:
            return "❌ max_results must be 1-20"
        
        # Query ChromaDB
        # results = chroma_client.collection.query(...)
        # return formatted_results
        
        return "✅ Search successful"  # Placeholder
    except Exception as e:
        return f"⚠️ Search error: {str(e)}"

# 3. In your agent loop
response = ollama.chat(model="qwen2.5:7b", messages=[...], tools=[...])

if response.message.tool_calls:
    for tool_call in response.message.tool_calls:
        if tool_call.function.name == "search_runbooks":
            try:
                # Validate
                args = tool_call.function.arguments
                validated = SearchRunbooksInput(**args)
                
                # Execute
                result = search_runbooks_safe(
                    query=validated.query,
                    max_results=validated.max_results
                )
            except ValidationError as e:
                result = f"❌ Invalid arguments: {e.errors()[0]['msg']}"
            
            # Return result to LLM
            # ... inject into messages ...
```

---

## 📚 **Key Takeaways**

1. **BaseModel** = Type-validated Python class
2. **Field()** = Add constraints (min/max, required/optional, defaults)
3. **ValidationError** = Catch and handle bad data gracefully
4. Use `try/except` to return error strings to LLM (not crashes)
5. Always validate LLM-generated data before using it

---

## 🔗 **Learning Resources**

- **Official Docs:** https://pydantic.dev/docs/validation/latest/get-started/
- **Field Reference:** https://pydantic.dev/docs/validation/latest/concepts/fields/
- **Validators Guide:** https://pydantic.dev/docs/validation/latest/concepts/validators/
- **Common Types:** https://pydantic.dev/docs/validation/latest/concepts/types/

---

## 💡 **Next Steps for Your Project**

1. **Install Pydantic:** `pip install pydantic`
2. **Create `src/validators.py`:**
   ```python
   from pydantic import BaseModel, Field
   
   class SearchRunbooksInput(BaseModel):
       query: str = Field(..., min_length=3, max_length=100)
       max_results: int = Field(default=5, ge=1, le=20)
   ```
3. **Test it:** Write unit tests for valid/invalid inputs
4. **Integrate:** Use in your agent loop (see practical example above)

---

## 🧪 **Quick Practice Exercises**

### Exercise 1: Create a model for incident severity
```python
# TODO: Define a model where:
# - incident_id: required string, 5-20 chars
# - severity: required, must be "low", "medium", "high", or "critical"
# - contact: optional string
```

### Exercise 2: Add error handling
```python
# TODO: Try creating an incident with invalid severity
# Catch ValidationError and print the error message
```

### Exercise 3: Validate tool args
```python
# TODO: Simulate LLM passing bad query args and catch the error
```

---

## 🎯 **For Your Specific Use Case**

Your SRE agent needs validation at **exactly one place**: when LLM-generated JSON arguments hit your `search_runbooks` function.

```
LLM generates JSON → Pydantic validates → Tool executes OR returns error
```

That's the pattern. Master it, and you'll catch 99% of hallucination bugs before they crash your agent.

**You're ready to implement Phase 3!** 🚀
