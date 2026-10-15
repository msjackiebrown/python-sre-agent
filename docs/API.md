# API Reference: Programmatic Usage

How to use the SRE Agent as a library in your own code.

---

## Quick Example

```python
from src.agent import react_agent

# Single query
response = react_agent("Database connection timeout")
print(response)
```

---

## Main API: `react_agent()`

### Function Signature

```python
def react_agent(
    user_query: str,
    max_iterations: int = 5,
    verbose: bool = False
) -> str:
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_query` | `str` | **Required** | The incident/issue description (e.g., "Database timeout") |
| `max_iterations` | `int` | 5 | Maximum ReAct loop cycles. Prevents infinite loops. |
| `verbose` | `bool` | False | Print iteration details for debugging |

### Returns

**Type:** `str`

**Content:** Formatted response with:
- Matching runbook IDs
- Severity levels (HIGH/MEDIUM/LOW)
- Escalation contacts
- Recommended next steps

### Raises

| Exception | Cause | Example |
|-----------|-------|---------|
| `ConnectionError` | Ollama not running | "❌ Ollama is not running at http://localhost:11434" |
| `RuntimeError` | Model not available | "❌ Model 'qwen2.5:7b' not found" |
| `Exception` | Unexpected error in tool execution | Tool result injection fails |

### Examples

#### Basic Query
```python
from src.agent import react_agent

response = react_agent("Database connection timeout")
print(response)
```

**Output:**
```
Found 3 runbooks for database connection issues...
[Details about INCIDENT-001, INCIDENT-003, INCIDENT-006]
```

#### Debugging with Verbose
```python
response = react_agent(
    "Database timeout",
    max_iterations=5,
    verbose=True  # Print each iteration
)
```

**Output:**
```
🔄 Iteration 1/5
   LLM Response: I should search for database issues...
   → Tool call: search_runbooks(query='database timeout', max_results=3)
   ← Result: ✅ Found 3 runbooks...

🔄 Iteration 2/5
   LLM Response: These runbooks cover the issue. Let me format...
   → No more tool calls. Returning final answer.

Agent Response:
[Final formatted answer]
```

#### Multiple Queries in Sequence
```python
queries = [
    "Database connection timeout",
    "Memory usage growing",
    "API connection refused"
]

for query in queries:
    print(f"\nQuery: {query}")
    response = react_agent(query)
    print(f"Response: {response[:100]}...")
```

#### With Error Handling
```python
from src.agent import react_agent

try:
    response = react_agent("Help with database issue")
    print(response)
except ConnectionError as e:
    print(f"Connection error: {e}")
    # Ollama not running
except RuntimeError as e:
    print(f"Model error: {e}")
    # Model not available
except Exception as e:
    print(f"Unexpected error: {e}")
    # Something else went wrong
```

---

## Helper Functions

### `check_ollama_connection()`

Verify Ollama is running at the configured endpoint.

```python
from src.agent import check_ollama_connection

try:
    check_ollama_connection()
    print("✅ Ollama is running")
except ConnectionError as e:
    print(f"❌ {e}")
```

**Parameters:** None

**Returns:** `bool` (True if connected)

**Raises:** `ConnectionError` with helpful message

---

### `ensure_model_available(model: str)`

Verify the requested model is available.

```python
from src.agent import ensure_model_available

try:
    ensure_model_available("qwen2.5:7b")
    print("✅ Model ready")
except RuntimeError as e:
    print(f"❌ {e}")
```

**Parameters:**
- `model` (str): Model name (e.g., "qwen2.5:7b")

**Returns:** None

**Raises:** `RuntimeError` if model not found

---

### `seed_runbooks(data_dir: str)`

Load runbooks from filesystem into ChromaDB.

```python
from src.db import seed_runbooks

collection, count = seed_runbooks(data_dir="src/data")
print(f"Loaded {count} runbooks")
```

**Parameters:**
- `data_dir` (str, optional): Path to directory with .md files. Default: "src/data"

**Returns:** Tuple[`Collection`, `int`]
- `Collection`: ChromaDB collection object
- `int`: Number of runbooks loaded

---

### `search_runbooks(query: str, max_results: int = 5)`

Search for matching runbooks by keyword.

```python
from src.tools import search_runbooks

results = search_runbooks(query="database timeout", max_results=3)
print(results)
```

**Parameters:**
- `query` (str): Search query (3-100 characters)
- `max_results` (int, optional): Max results to return (1-20). Default: 5

**Returns:** `str` (formatted markdown with results)

**Raises:** `ValidationError` if arguments invalid

---

## Data Models: Pydantic

### `SearchRunbooksInput`

Validates arguments for `search_runbooks()`.

```python
from src.tools import SearchRunbooksInput

# Valid input
input = SearchRunbooksInput(
    query="database connection timeout",
    max_results=3
)

# Invalid input (too short)
try:
    input = SearchRunbooksInput(query="x")
except ValidationError as e:
    print(e)  # "query" must be at least 3 characters
```

**Fields:**
- `query` (str): Min 3, max 100 characters. Required.
- `max_results` (int): Min 1, max 20. Default: 5

---

## Configuration

### Environment Variables

```python
import os

# Ollama URL (defaults to localhost)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Model name (defaults to qwen2.5:7b)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
```

### Setting at Runtime

```python
import os

# Set before importing
os.environ["OLLAMA_HOST"] = "http://remote-ollama.example.com:11434"
os.environ["OLLAMA_MODEL"] = "llama2"

# Now import and use
from src.agent import react_agent
response = react_agent("Test query")
```

---

## Integration Examples

### Flask Web Service
```python
from flask import Flask, request, jsonify
from src.agent import react_agent

app = Flask(__name__)

@app.route("/troubleshoot", methods=["POST"])
def troubleshoot():
    data = request.json
    query = data.get("query")
    
    try:
        response = react_agent(query, verbose=False)
        return jsonify({"status": "success", "response": response})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000)
```

**Usage:**
```bash
curl -X POST http://localhost:5000/troubleshoot \
  -H "Content-Type: application/json" \
  -d '{"query": "Database connection timeout"}'
```

### Async Runner
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.agent import react_agent

executor = ThreadPoolExecutor(max_workers=4)

async def async_query(query: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, react_agent, query)

async def main():
    results = await asyncio.gather(
        async_query("Database timeout"),
        async_query("Memory leak"),
        async_query("Connection refused")
    )
    
    for result in results:
        print(result)
        print("---")

asyncio.run(main())
```

### Batch Processing
```python
from src.agent import react_agent

queries = [
    "Database connection timeout",
    "Memory usage growing",
    "API rate limiting issues"
]

results = []
for query in queries:
    try:
        response = react_agent(query, verbose=False)
        results.append({
            "query": query,
            "status": "success",
            "response": response
        })
    except Exception as e:
        results.append({
            "query": query,
            "status": "error",
            "error": str(e)
        })

# Export results
import json
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

## Error Handling Best Practices

### Graceful Degradation
```python
from src.agent import react_agent, check_ollama_connection

def get_troubleshooting_help(query: str) -> str:
    """Get help, fallback gracefully if Ollama unavailable."""
    
    try:
        check_ollama_connection()
    except ConnectionError:
        return "⚠️ AI troubleshooting unavailable. Ollama not running. Try: ollama serve"
    
    try:
        return react_agent(query)
    except RuntimeError as e:
        return f"⚠️ {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"
```

### Retry Logic
```python
import time
from src.agent import react_agent

def query_with_retry(query: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            return react_agent(query)
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

---

## Performance Tips

### Reduce Verbosity for Speed
```python
# ❌ Slow: Verbose output for every query
response = react_agent(query, verbose=True)

# ✅ Fast: No debugging output
response = react_agent(query, verbose=False)
```

### Limit Iterations for Quick Answers
```python
# ❌ Slow: Allow up to 5 loops
response = react_agent(query, max_iterations=5)

# ✅ Fast: Force answer after 2 loops
response = react_agent(query, max_iterations=2)
```

### Cache Results
```python
from functools import lru_cache
from src.agent import react_agent

@lru_cache(maxsize=32)
def cached_query(query: str) -> str:
    """Cache agent responses for identical queries."""
    return react_agent(query)

# First call: runs agent (~2-3 sec)
result1 = cached_query("Database timeout")

# Second call with same query: returns cached (~1ms)
result2 = cached_query("Database timeout")
```

---

## Troubleshooting API Issues

### Import Error
```python
# ❌ Wrong: Assumes current directory
from agent import react_agent

# ✅ Correct: Use absolute or relative imports
from src.agent import react_agent
```

### Model Not Found
```python
from src.agent import ensure_model_available, OLLAMA_MODEL

try:
    ensure_model_available(OLLAMA_MODEL)
except RuntimeError:
    print(f"Pull the model: ollama pull {OLLAMA_MODEL}")
```

### Type Error
```python
# ❌ Wrong type
response = react_agent(123)  # int instead of str

# ✅ Correct
response = react_agent("123")  # str
```

---

## See Also

- [GETTING_STARTED.md](./GETTING_STARTED.md) — Installation and CLI usage
- [TESTING.md](./TESTING.md) — How to test the agent
- [ARCHITECTURE.md](./ARCHITECTURE.md) — System design details
