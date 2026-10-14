# Getting Started with the SRE Agent

Quick installation and first run in 5 minutes.

---

## Prerequisites

- **Python:** 3.10 or later
- **RAM:** 8GB+ (for Ollama inference)
- **Disk:** 5GB+ (for model downloads)
- **OS:** macOS, Linux, or Windows (with WSL optional)

---

## Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/msjackiebrown/python-sre-agent.git
cd python-sre-agent
```

### Step 2: Create Virtual Environment (Optional but Recommended)
```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**What gets installed:**
- `ollama` — Python client for Ollama API
- `chromadb>=0.4.0` — Vector database (in-memory)
- `streamlit>=1.57` — Web UI framework
- `pydantic>=2.0` — Data validation
- `pytest` — Testing framework
- `requests` — HTTP library (for Ollama API)
- `pyyaml` — YAML frontmatter parsing

### Step 4: Install Ollama (If Not Already Installed)

**macOS:**
```bash
brew install ollama
# or download from https://ollama.ai
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download installer from [ollama.ai](https://ollama.ai)

### Step 5: Start Ollama Server
```bash
ollama serve
```

This starts the HTTP API at `http://localhost:11434`.

**In a new terminal, pull the model:**
```bash
ollama pull qwen2.5:7b
# Downloads ~4.7 GB (first time only)
```

---

## Quick Start: Three Ways to Use

### Option 1: Web UI (Recommended for Recruiters)
```bash
streamlit run src/main.py
```

Opens browser to `http://localhost:8501`. Type your incident query in the chat box.

**Features:**
- ✅ Chat-like interface (newest messages at bottom)
- ✅ Conversation history maintained
- ✅ Connection status in sidebar
- ✅ Collapsible help panels

### Option 2: Command-Line (Testing/Debugging)
```bash
python src/agent.py
```

Runs 3 test queries through the ReAct loop with verbose iteration output.

**Output shows:**
```
🚀 Phase 4: LLM Integration with ReAct Pattern
...
🔄 Iteration 1/5
   LLM Response: I should search for database runbooks...
   → Tool call: search_runbooks(query='database timeout', max_results=3)
   ← Result: ✅ Found 3 runbooks...

🤖 Agent Response:
[Formatted runbook details with escalation paths]
```

### Option 3: Python API (Programmatic)
```python
from src.agent import react_agent

# Single query
response = react_agent("Database connection timeout")
print(response)

# With debugging
response = react_agent(
    "Database connection timeout",
    max_iterations=5,
    verbose=True  # Shows iteration details
)
```

---

## Configuration: Local vs. Remote Ollama

### Local Ollama (Default)
```bash
# Already defaults to http://localhost:11434
streamlit run src/main.py
```

### Remote Ollama
```bash
# Set before running:
export OLLAMA_HOST=http://api.your-server.com:11434
export OLLAMA_MODEL=qwen2.5:7b

streamlit run src/main.py
```

**Windows PowerShell:**
```powershell
$env:OLLAMA_HOST = "http://api.your-server.com:11434"
$env:OLLAMA_MODEL = "qwen2.5:7b"

streamlit run src/main.py
```

The app automatically:
1. Connects to the configured Ollama URL
2. Verifies the model is available
3. Loads 7 sample runbooks into ChromaDB
4. Starts processing queries

---

## Verify Installation

### Check Python Version
```bash
python --version
# Should be 3.10+
```

### Check Dependencies
```bash
pip list | grep -E "ollama|chromadb|streamlit|pydantic"
```

### Check Ollama Connection
```bash
curl http://localhost:11434/api/tags
# Should return JSON with available models
```

### Run Tests
```bash
pytest tests/ -v
# Should show:
# test_db.py: 8 PASSED
# test_tools.py: 15 PASSED
```

---

## Example Queries to Try

Test the agent with these incident scenarios:

1. **Database Issue:**
   ```
   "Database connection timeout errors when traffic spikes"
   ```

2. **Performance Problem:**
   ```
   "Memory usage is growing in the application"
   ```

3. **API Error:**
   ```
   "I'm getting connection refused when talking to the database"
   ```

4. **Vague Issue (tests keyword matching):**
   ```
   "Something is slow"
   ```

Each query triggers the ReAct loop:
- Agent searches 7 runbooks in ChromaDB
- Returns matching incidents with severity levels
- Provides escalation contacts
- Suggests next troubleshooting steps

---

## Troubleshooting

### "Ollama is not running"
**Error:** Connection error when starting the app

**Fix:**
```bash
# Start Ollama server (in a separate terminal)
ollama serve

# Then run your app in another terminal
streamlit run src/main.py
```

### "Model not found: qwen2.5:7b"
**Error:** Agent can't find the model

**Fix:**
```bash
# Pull the model
ollama pull qwen2.5:7b

# Or use a different model
export OLLAMA_MODEL=llama2
streamlit run src/main.py
```

**Check available models:**
```bash
curl http://localhost:11434/api/tags | python -m json.tool
```

### "Connection refused"
**Error:** Can't reach Ollama at the configured URL

**Check:**
1. Is Ollama running? (`ps aux | grep ollama`)
2. Is URL correct? (`echo $OLLAMA_HOST`)
3. Is firewall blocking the port?

**Debug:**
```bash
curl -v http://localhost:11434/api/tags
# Should show HTTP 200
```

### "ModuleNotFoundError: No module named 'streamlit'"
**Error:** Streamlit not installed

**Fix:**
```bash
pip install -r requirements.txt
# Or just: pip install streamlit
```

---

## Next Steps

- **Learn the architecture:** See [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Understand design decisions:** See [DESIGN_DECISIONS.md](./DESIGN_DECISIONS.md)
- **Run tests:** See [TESTING.md](./TESTING.md)
- **Use as API:** See [API.md](./API.md)
- **Deploy to production:** See [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## Tips for Best Results

✅ **Be specific in queries** — "database timeout during peak load" beats "database slow"

✅ **Try multiple searches** — If results aren't relevant, rephrase with different keywords

✅ **Check severity levels** — HIGH/MEDIUM/LOW help prioritize escalations

✅ **Follow escalation contacts** — Each runbook includes who to page and when

✅ **Keep ChromaDB in mind** — This uses vector similarity search, not keyword matching
   - "database connection error" will find incident runbooks about database issues
   - More descriptive = better matches
