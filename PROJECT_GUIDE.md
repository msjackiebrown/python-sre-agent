# 📘 PROJECT GUIDE: Building a Tool-Using Agent

This guide contains the architectural concepts, resources, and critical design questions you need to answer as you implement the `python-sre-agent`. 

## 1. The Core Concept: "The ReAct Loop"
You are building an **Agent**, not just a Chatbot. A chatbot asks/answers. An Agent *Reasons*, *Acts* (calls tools), and then *Observes* the result.

**Your implementation loop will look like this:**
1.  **User Input:** "Why is the SWIFT API timing out?"
2.  **LLM Thought:** *"I don't know, but I have a tool called `search_runbooks`."* → Returns JSON schema.
3.  **Python Code:** Intercepts JSON -> Runs `search_runbooks()` against ChromaDB -> Gets result.
4.  **Tool Result:** Injected back into LLM context as `<tool_response> ... </tool_response>`.
5.  **Final Answer:** LLM synthesizes the text using that data.

## 2. Key Resources to Study
- **[Ollama Tool Calling Docs](https://docs.ollama.com/capabilities/tool-calling#python):** *Critical.* Read how `chat_request.messages[].tool_calls` works in the raw JSON response. This is where your branching logic lives.
- **[ChromaDB Quickstart (In-Memory)](https://www.trychroma.com/docs/embeddings/overview):** Look for `chromadb.Client()` vs `chromadb.PersistentClient()`. You want the first one.
- **[LangChain Tool Calling Tutorials](https://python.langchain.com/docs/how_to/#tools):** Even though we aren't using LangChain, their *diagrams* of how agents handle tool outputs are excellent for understanding the pattern.

## 3. Design Questions to Answer (Notes)
As you code, pause and document the answers to these in `docs/notes.md`:

### Q1: Tool Schema Precision
*How strictly do we define the tool description?* 
- If your tool description is vague ("searches data"), the LLM might call it for simple greetings.
- *Task:* Draft a "Golden Description" for your runbook search tool that forces the LLM to only use it when it detects keywords like "incident", "error", or "SOP".

### Q2: Handling Hallucinations in Tool Args
*What if the LLM passes bad arguments?*
- Ollama might try to call `search_runbooks(query="")` or pass extra unexpected keys.
- *Task:* Design your Python wrapper functions to validate inputs (e.g., using Pydantic or simple `if not query: return "Error..."`) before hitting the database.

### Q3: The "Max Iterations" Trap
*What if the LLM gets stuck in a loop calling tools forever?*
- If the runbook doesn't answer the question, will the LLM call the search tool again and again?
- *Task:* Implement a `max_tool_calls` counter in your `agent.py` loop. If hit > 3 times, force a direct text response or a "I couldn't find the answer" fallback.

### Q4: ChromaDB Seeding Strategy
*Where does the embedding happen?*
- Do we embed *all* runbooks on startup (fast query, slow start)? Or embed *on-the-fly* as they are added?
- *Recommendation:* Since it's mock data, do a one-time bulk add in `main()` at launch.

## 4. Portfolio "Flex" Points (Why this gets hired)
1. **Local Inference:** You prove you can build complex AI apps without $50/mo API bills.
2. **Tool Safety:** By catching JSON errors and tool failures, you show you write *production-ready* code, not just playground scripts.
3. **Domain Expertise:** The mock data proves you understand *Enterprise SRE workflows* (SWIFT, PCI-DSS), bridging the gap between AI dev and Business Ops.

---
**Status:** Ready for Implementation Phase 3.