# Ollama OpenAI-Compatible API Reference

## Overview

Ollama exposes an OpenAI-compatible REST API on port 11434. This means:
- **Local**: `http://localhost:11434`
- **Remote**: `http://your-server:11434`

Both work the same way—just the URL changes.

---

## 1. Core Endpoints

### `/api/tags` — List Available Models

**Request:**
```bash
curl http://localhost:11434/api/tags
```

**Python (requests):**
```python
import requests

response = requests.get("http://localhost:11434/api/tags")
models = response.json()["models"]
# [{"name": "qwen2.5:7b", "size": 4700000000, ...}, ...]
```

**Response:**
```json
{
  "models": [
    {
      "name": "qwen2.5:7b",
      "modified_at": "2025-01-15T10:23:45.123456789Z",
      "size": 4700000000,
      "digest": "sha256:abc123..."
    }
  ]
}
```

---

### `/api/chat` — Send a Message (with Tools Support)

**Request (curl):**
```bash
curl http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "user",
        "content": "Say hello in one sentence."
      }
    ],
    "stream": false
  }'
```

**Python (requests):**
```python
import requests
import json

payload = {
    "model": "qwen2.5:7b",
    "messages": [
        {"role": "user", "content": "Say hello in one sentence."}
    ],
    "stream": False
}

response = requests.post(
    "http://localhost:11434/api/chat",
    json=payload,
    headers={"Content-Type": "application/json"}
)

result = response.json()
print(result["message"]["content"])
```

**Python (ollama library - recommended):**
```python
from ollama import chat

response = chat(
    model="qwen2.5:7b",
    messages=[
        {"role": "user", "content": "Say hello in one sentence."}
    ],
    stream=False
)

print(response.message.content)
```

**Response:**
```json
{
  "model": "qwen2.5:7b",
  "created_at": "2025-01-15T10:24:12.345678901Z",
  "message": {
    "role": "assistant",
    "content": "Hello! I'm here to help you with any questions or tasks."
  },
  "done": true,
  "total_duration": 2500000000,
  "load_duration": 1000000000,
  "prompt_eval_count": 15,
  "eval_count": 20,
  "eval_duration": 1500000000
}
```

---

## 2. With Function Calling (Tools)

### Request Structure

The `tools` parameter is OpenAI-compatible. Pass function definitions:

**curl:**
```bash
curl http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [
      {
        "role": "user",
        "content": "Search for database timeout issues"
      }
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "search_runbooks",
          "description": "Search the runbook database",
          "parameters": {
            "type": "object",
            "properties": {
              "query": {
                "type": "string",
                "description": "Search query (3-100 characters)"
              },
              "max_results": {
                "type": "integer",
                "description": "Max results to return"
              }
            },
            "required": ["query"]
          }
        }
      }
    ],
    "stream": false
  }'
```

**Python (ollama library):**
```python
from ollama import chat
from tools import search_runbooks  # Direct function reference!

response = chat(
    model="qwen2.5:7b",
    messages=[
        {"role": "user", "content": "Search for database timeout issues"}
    ],
    tools=[search_runbooks],  # ← Pass function directly!
    stream=False
)

# If Ollama called a tool:
if response.message.tool_calls:
    for tool_call in response.message.tool_calls:
        print(f"Tool: {tool_call.function.name}")
        print(f"Args: {tool_call.function.arguments}")
        # Execute tool here...
```

**Response with Tool Call:**
```json
{
  "model": "qwen2.5:7b",
  "message": {
    "role": "assistant",
    "content": "I'll search for database timeout issues.",
    "tool_calls": [
      {
        "function": {
          "name": "search_runbooks",
          "arguments": {
            "query": "database timeout",
            "max_results": 3
          }
        }
      }
    ]
  },
  "done": true
}
```

---

## 3. Configuration Patterns

### Environment Variables

Set once, affects all code:

```bash
# Local (default)
export OLLAMA_HOST=http://localhost:11434

# Remote
export OLLAMA_HOST=http://api.msjackiebrown.net:11434

# Then any Python code using `ollama.chat()` automatically uses this URL
```

### Python Runtime

```python
import os
from ollama import chat

# Defaults to http://localhost:11434
# Respects OLLAMA_HOST env var if set

# Can also override programmatically:
os.environ["OLLAMA_HOST"] = "http://api.example.com:11434"

response = chat(model="qwen2.5:7b", messages=[...])
```

---

## 4. Error Handling

### Connection Error

```python
import requests

try:
    resp = requests.get(
        "http://localhost:11434/api/tags",
        timeout=5
    )
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} {resp.text}")
except requests.ConnectionError:
    print("Ollama not running")
except requests.Timeout:
    print("Ollama not responding (timeout)")
```

### Model Not Found

```python
response = requests.get("http://localhost:11434/api/tags")
models = response.json()["models"]
model_names = [m["name"] for m in models]

if "qwen2.5:7b" not in model_names:
    print(f"Model not found. Available: {model_names}")
    print("Pull it: ollama pull qwen2.5:7b")
```

---

## 5. Quick Reference: curl → Python Mapping

| Step | curl | Python (requests) | Python (ollama) |
|------|------|-------------------|-----------------|
| **List models** | `curl http://localhost:11434/api/tags` | `requests.get(.../api/tags)` | N/A (not needed) |
| **Chat simple** | `curl -X POST .../api/chat -d '{"model": "...", "messages": [...], "stream": false}'` | `requests.post(.../api/chat, json={...})` | `chat(model="...", messages=[...])` |
| **Chat with tools** | Same but add `"tools": [...]` | Same but add `tools` key | `chat(..., tools=[func1, func2])` |
| **Stream mode** | `"stream": true` | `stream=True` in json | `stream=True` parameter |

---

## 6. Our Agent's Usage

In [agent.py](../src/agent.py), we use the `ollama` library which:
1. Reads `OLLAMA_HOST` env var (defaults to `http://localhost:11434`)
2. Makes HTTP POST requests to `/api/chat` endpoint
3. Automatically serializes Python functions as OpenAI-compatible tool schemas
4. Handles streaming/non-streaming transparently

**Example from our code:**
```python
from ollama import chat
from tools import search_runbooks  # Python function

# This makes HTTP request equivalent to the curl above ↑
response = chat(
    model=OLLAMA_MODEL,  # "qwen2.5:7b"
    messages=messages,
    tools=[search_runbooks],  # Direct function, Ollama introspects docstring + params
    temperature=0.3,
    stream=False  # Don't stream responses
)
```

---

## 7. Testing Your Setup

### Test 1: Can you reach Ollama?
```bash
# Local
curl http://localhost:11434/api/tags

# Remote
curl http://api.msjackiebrown.net:11434/api/tags
```

**Expected output:** JSON with list of models (even if empty)

### Test 2: Is a model available?
```bash
# Check response from Test 1
# Look for "qwen2.5:7b" in the models list

# If not there, pull it:
ssh api.msjackiebrown.net
ollama pull qwen2.5:7b
```

### Test 3: Can you chat?
```bash
curl http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'
```

**Expected output:** JSON with assistant's response

### Test 4: Run our agent
```bash
python src/agent.py
```

Should:
1. Show configuration
2. Connect to Ollama
3. Verify model exists
4. Load runbooks
5. Run ReAct loop with tool calls

---

## 8. Key Takeaways

✅ **Ollama is OpenAI-compatible** — same HTTP API, same JSON format  
✅ **Works local AND remote** — just change the URL  
✅ **The `ollama` library handles details** — we just pass functions as tools  
✅ **No manual schemas needed** — Ollama introspects Python functions  
✅ **Environment variables control everything** — set once, use everywhere
