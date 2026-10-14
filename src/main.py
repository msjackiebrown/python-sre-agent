"""main.py — Streamlit UI for SRE Agent

Phase 4+ Presentation Tier: Web interface for the ReAct agent

This app:
1. Provides a chat-like interface for querying the SRE agent
2. Displays runbook search results with escalation paths
3. Maintains conversation history with proper UX (newest at bottom)
4. Shows Ollama connection status
5. Auto-scrolls to new messages
"""

import streamlit as st
from agent import react_agent, check_ollama_connection, ensure_model_available, OLLAMA_HOST, OLLAMA_MODEL

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="SRE Troubleshooting Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for better scrolling behavior
st.markdown("""
<style>
    /* Make chat container scrollable */
    .chat-container {
        height: calc(100vh - 300px);
        overflow-y: auto;
        padding: 1rem;
        border-radius: 8px;
        background-color: #f0f2f6;
    }
    
    /* Better message styling */
    .user-message {
        margin: 1rem 0;
        padding: 1rem;
        background-color: #dbeafe;
        border-left: 4px solid #3b82f6;
        border-radius: 4px;
    }
    
    .assistant-message {
        margin: 1rem 0;
        padding: 1rem;
        background-color: #f3f4f6;
        border-left: 4px solid #6b7280;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR — Configuration & Status
# ============================================================================

st.sidebar.title("⚙️ Configuration")
st.sidebar.write(f"**Ollama URL:** `{OLLAMA_HOST}`")
st.sidebar.write(f"**Model:** `{OLLAMA_MODEL}`")

# Connection status
try:
    check_ollama_connection()
    ensure_model_available(OLLAMA_MODEL)
    st.sidebar.success("✅ Connected to Ollama")
except Exception as e:
    st.sidebar.error(f"❌ Connection Error\n\n{str(e)}")
    st.stop()

st.sidebar.divider()

# Clear conversation button
if st.sidebar.button("🗑️ Clear Conversation", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

st.sidebar.divider()
st.sidebar.info(
    """
    **How to use:**
    1. Type your incident or issue in the text box at the bottom
    2. The agent will search runbooks and provide solutions
    3. Follow the escalation path if needed
    
    **Tips:**
    - Be specific: "database timeout" works better than "slow"
    - Try different keywords if no results
    - Always check the severity level and escalation contact
    """
)

# ============================================================================
# MAIN PAGE — Chat Interface
# ============================================================================

st.title("🤖 SRE Troubleshooting Agent")
st.markdown("Ask me about operational issues, and I'll search the runbook database for solutions.")

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# ============================================================================
# CONVERSATION HISTORY — Display in Chronological Order
# ============================================================================

# Container for messages (scrollable, newest at bottom)
with st.container():
    # Display all messages in order (oldest → newest)
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>👤 You:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:  # assistant
            st.markdown(f"""
            <div class="assistant-message">
                <strong>🤖 Agent:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Placeholder for scroll anchor (forces view to bottom)
    st.markdown("<div id='scroll-anchor'></div>", unsafe_allow_html=True)

# ============================================================================
# USER INPUT & AGENT PROCESSING — At Bottom
# ============================================================================

st.divider()

# Always show input at bottom
col1, col2 = st.columns([0.85, 0.15])

with col1:
    user_query = st.text_input(
        "Describe your issue or incident...",
        placeholder="e.g., 'Database connection timeout errors' or 'Memory usage growing in app'",
        label_visibility="collapsed"
    )

with col2:
    send_button = st.button("Send ➤", use_container_width=True)

# Process query when user sends message
if send_button and user_query:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Process with agent
    with st.spinner("🔍 Searching runbooks and analyzing..."):
        try:
            # Call the ReAct agent
            response = react_agent(user_query, max_iterations=5, verbose=False)
            
            # Add agent response to history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Rerun to display new messages and scroll to bottom
            st.rerun()
            
        except Exception as e:
            error_msg = f"❌ Error: {type(e).__name__}: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.error(error_msg)

# ============================================================================
# FOOTER — Help & Reference
# ============================================================================

st.divider()
col1, col2 = st.columns(2)

with col1:
    with st.expander("📚 Quick Reference"):
        st.markdown("""
        - **Runbook ID**: Unique identifier (e.g., INCIDENT-001)
        - **Severity**: HIGH/MEDIUM/LOW impact level
        - **Escalation**: Who to contact and when
        - **Keywords**: Search terms that matched
        """)

with col2:
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        - **Model not found**: Check model availability on Ollama
        - **No results**: Try different keywords or be more specific
        - **Connection fails**: Verify `OLLAMA_HOST` and Ollama is running
        """)
