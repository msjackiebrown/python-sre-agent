"""src/agent.py — ReAct loop for SRE troubleshooting agent.

Phase 4: LLM Integration using Ollama Function Calling + ReAct Pattern

This module:
1. Connects to Ollama via OpenAI-compatible API (default: http://localhost:11434)
2. Seeds the ChromaDB with runbooks
3. Implements the ReAct loop: Thought → Action → Observation → Reasoning

Ollama's function calling directly introspects Python functions:
- Docstrings become tool descriptions
- Parameters become schema (no manual JSON needed)
- OpenAI-compatible API works with local or remote instances

Configuration:
- Local: OLLAMA_HOST=http://localhost:11434 (default)
- Remote: OLLAMA_HOST=http://api.msjackiebrown.net:11434 (example)
"""

import os
import requests
from ollama import chat
from tools import search_runbooks
from db import seed_runbooks


# ============================================================================
# OLLAMA CONNECTION — Setup & Verification
# ============================================================================

# OpenAI-compatible Ollama API endpoint
# Default: localhost for local installs
# Set OLLAMA_HOST env var to override (e.g., http://api.msjackiebrown.net:11434)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Model to use for ReAct loop
# Must be available on the Ollama instance
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


def check_ollama_connection() -> bool:
    """Verify Ollama is running and accessible via OpenAI-compatible API.
    
    Returns:
        True if connected, False otherwise
        
    Raises:
        ConnectionError with helpful message if Ollama isn't running
    """
    try:
        # Use OpenAI-compatible /api/tags endpoint (works for any Ollama instance)
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if resp.status_code == 200:
            return True
    except requests.RequestException:
        pass
    
    raise ConnectionError(
        f"❌ Ollama is not running at {OLLAMA_HOST}\n"
        f"   Options:\n"
        f"   1. Local: Run 'ollama serve' (default port 11434)\n"
        f"   2. Remote: Set OLLAMA_HOST=http://your-server:11434\n"
        f"   3. Check: curl {OLLAMA_HOST}/api/tags"
    )


def ensure_model_available(model: str) -> None:
    """Verify the required model is available via OpenAI-compatible API.
    
    Args:
        model: Model name (e.g., "qwen2.5:7b")
        
    Raises:
        RuntimeError if model is not available
    """
    print(f"📥 Checking if {model} is available...")
    
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            available_models = [m.get("name", "") for m in models]
            
            # Check if requested model is available
            if any(model in m for m in available_models):
                print(f"✅ Model {model} ready")
                return
            
            # Model not found - provide helpful error
            raise RuntimeError(
                f"❌ Model '{model}' not found on {OLLAMA_HOST}\n"
                f"   Available models: {', '.join(available_models) if available_models else 'none'}\n"
                f"   To add it: ollama pull {model}"
            )
    except requests.RequestException as e:
        raise RuntimeError(
            f"❌ Could not check models on {OLLAMA_HOST}\n"
            f"   Error: {e}"
        )


# ============================================================================
# SYSTEM PROMPT — Agent's Role & Behavior
# ============================================================================

SYSTEM_PROMPT = """You are an SRE troubleshooting assistant powered by a runbook database.

Your role:
- Help users resolve incidents and operational problems
- Search the runbook database for relevant procedures
- Provide clear, actionable steps
- Always include escalation paths (who to page, when)
- Prioritize safety (no destructive actions without explicit warning)

When a user reports an issue:
1. THINK: What is the core problem? What keywords should I search?
2. ACT: Use search_runbooks to find relevant runbooks
3. OBSERVE: What runbooks matched? Are there results?
4. REASON: How should I present this? Do I need more info?
5. REPEAT or ANSWER: If needed, refine search. Otherwise, return formatted response.

Key guidelines:
- Search for specific keywords (e.g., "database timeout", "memory leak")
- If no results, try different keywords or suggest related topics
- Always mention the runbook ID and severity
- Format responses with clear steps and contact info
- Be concise: max 3 runbooks per response"""


# ============================================================================
# REACT LOOP — Core Agent Implementation
# ============================================================================

def react_agent(user_query: str, max_iterations: int = 5, verbose: bool = False) -> str:
    """ReAct loop for SRE troubleshooting.
    
    Implements: Thought → Action → Observation → Reasoning loop
    
    Args:
        user_query: User's question/issue (e.g., "database connection timeout")
        max_iterations: Max loop iterations (prevents infinite loops)
        verbose: Print iteration details for debugging
        
    Returns:
        Formatted response with runbook info or error message
        
    Example:
        >>> answer = react_agent("I'm getting connection refused errors")
        >>> print(answer)
        I found 2 relevant runbooks...
    """
    
    # Initialize message history with system prompt
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    
    # Track iterations for safety + logging
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        if verbose:
            print(f"\n🔄 Iteration {iteration}/{max_iterations}")
        
        # ─────────────────────────────────────────────────────────────
        # STEP 1: LLM Thinks & Decides (with access to tools)
        # ─────────────────────────────────────────────────────────────
        # Pass search_runbooks DIRECTLY - Ollama introspects it
        response = chat(
            model=OLLAMA_MODEL,  # ← Use configured model
            messages=messages,
            tools=[search_runbooks],  # ← Pass function, not schema!
            stream=False
        )
        
        if verbose:
            print(f"   LLM Response: {response.message.content[:100]}...")
        
        # ─────────────────────────────────────────────────────────────
        # STEP 2: Check if LLM Decided to Use a Tool
        # ─────────────────────────────────────────────────────────────
        if not response.message.tool_calls:
            # LLM decided to stop and return final answer
            if verbose:
                print(f"   → No tool calls. Returning final answer.")
            return response.message.content
        
        # ─────────────────────────────────────────────────────────────
        # STEP 3: Execute Tool(s) → Observation
        # ─────────────────────────────────────────────────────────────
        for tool_call in response.message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments
            
            if verbose:
                print(f"   → Tool call: {tool_name}({tool_args})")
            
            # Execute tool with auto-parsed arguments
            try:
                result = search_runbooks(**tool_args)
                observation_content = result
                observation_status = "success"
            except Exception as e:
                observation_content = f"❌ Tool error: {type(e).__name__}: {str(e)}"
                observation_status = "error"
            
            if verbose:
                result_preview = observation_content[:80].replace("\n", " ")
                print(f"   ← Result: {result_preview}...")
            
            # ─────────────────────────────────────────────────────────
            # STEP 4: Add Observation to Message History
            # ─────────────────────────────────────────────────────────
            # Add LLM's thinking to messages
            messages.append({"role": "assistant", "content": response.message.content})
            
            # Add tool result using standard Ollama format
            messages.append({
                "role": "tool",
                "tool_name": tool_name,
                "content": observation_content
            })
    
    # Safety: Reached max iterations
    if verbose:
        print(f"\n⚠️  Max iterations ({max_iterations}) reached")
    
    return f"⚠️ Max iterations ({max_iterations}) reached. Last response: {response.message.content}"


# ============================================================================
# MODULE ENTRY POINT — Test the Agent
# ============================================================================

if __name__ == "__main__":
    print("🚀 Phase 4: LLM Integration with ReAct Pattern")
    print("=" * 70)
    
    # Show configuration
    print(f"\n⚙️  Configuration:")
    print(f"   Ollama URL: {OLLAMA_HOST}")
    print(f"   Model: {OLLAMA_MODEL}")
    print(f"   (Set OLLAMA_HOST or OLLAMA_MODEL env vars to override)")
    
    # Step 1: Verify Ollama Connection
    print(f"\n🔗 Connecting to Ollama...")
    try:
        check_ollama_connection()
        print(f"✅ Connected to Ollama")
    except ConnectionError as e:
        print(str(e))
        exit(1)
    
    # Step 2: Ensure Model is Available
    try:
        ensure_model_available(OLLAMA_MODEL)
    except RuntimeError as e:
        print(f"❌ {e}")
        exit(1)
    
    # Step 3: Initialize Database
    print("\n📚 Seeding runbooks...")
    collection, count = seed_runbooks()
    print(f"✅ Loaded {count} runbooks into ChromaDB\n")
    
    # Test queries
    test_queries = [
        "Database connection timeout errors",
        "I'm getting 'connection refused' when talking to the database",
        "Memory usage is growing in my application"
    ]
    
    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"📝 User Query: {query}")
        print(f"{'='*70}")
        
        answer = react_agent(query, verbose=True)
        
        print(f"\n🤖 Agent Response:")
        print(f"{'-'*70}")
        print(answer)
        print(f"{'-'*70}")
