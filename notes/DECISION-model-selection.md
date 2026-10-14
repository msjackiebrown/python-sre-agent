---
title: DECISION - Dual-Model Portfolio Strategy for Python SRE Agent
subject: Model Selection & Deployment Strategy
date: 2026-10-13
status: ✅ APPROVED
tags: [model-selection, qwen, deployment-pragmatism, recruiter-facing, portfolio]
---

## 🎯 **THE DECISION: Dual-Model Portfolio Strategy**

**Primary Strategy:** Ship Qwen 2.5-7B in GitHub repo (recruiter-runnable), showcase Qwen 3.8-27B in YouTube video (demonstration-only).

**Rationale:** Pragmatic deployment optimization that mirrors real-world tradeoffs. Recruiters can actually *run* and test the agent. You demonstrate full capability without burdening them.

---

## 📊 **Model Comparison: 3 Candidates**

### **Option 1: Qwen 3.8-27B**
- **Size:** 18 GB | **Tool Calling:** ✅ | **Thinking:** ✅ | **Vision:** ✅
- **Pros:** 
  - ✅ Thinking process visible by default (portfolio wow factor)
  - ✅ Explicitly designed for agentic tasks
  - ✅ 256K context window
  - ✅ Strong tool calling reliability
  - ✅ Excellent coding/reasoning capabilities
- **Cons:** ⚠️ Requires 24GB+ RAM; ⚠️ slower on CPU (10-20 tokens/sec)
- **Use Case:** YouTube demonstration video (you control the narrative)

### **Option 2: Nemotron-3.5-Lightning-30B** (Alternate/Production)
- **Size:** 25 GB | **Tool Calling:** ✅ | **Thinking:** ✅ | **Vision:** ❌
- **Pros:**
  - ✅ MoE architecture (only 3B active parameters)
  - ✅ 1M token context (massive incident history capacity)
  - ✅ 30% faster than comparable models
  - ✅ Production-grade for agents
  - ✅ Better CPU throughput (25-35 tokens/sec)
- **Cons:** ⚠️ Requires 24GB+ RAM; ⚠️ no vision; ⚠️ MoE less efficient on CPU
- **Use Case:** Production deployments with throughput constraints (Phase 5 alternative)

### **Option 3: Qwen 2.5-7B** ⭐ **PRIMARY PORTFOLIO MODEL**
- **Size:** 4.7 GB | **Tool Calling:** ✅ | **Thinking:** ⚠️ Limited | **Vision:** ❌
- **Pros:**
  - ✅ Ultra-compact (runs on 8-10GB RAM)
  - ✅ Fast inference (50+ tokens/sec on CPU)
  - ✅ Perfect for recruiter hardware constraints
  - ✅ Tool calling is JSON-based (doesn't need thinking to work)
  - ✅ Great for Phase 2/3 prototyping
  - ✅ **Proves you understand deployment tradeoffs**
- **Cons:** ❌ No visible thinking process; ⚠️ limited agentic reasoning depth
- **Use Case:** GitHub portfolio (what recruiters will clone and run)

---

## 🚀 **RECOMMENDED STRATEGY: Dual-Model Approach**

### **Layer 1: GitHub Portfolio (Recruiter-Facing)**
**Model:** `Qwen 2.5-7B`
- Recruiters clone repo → `ollama run qwen2.5:7b` → Works in 5 minutes
- They see: ✅ Tool calling, ✅ Agent loop, ✅ ChromaDB retrieval, ✅ Responsive UX
- They experience: Fully functional SRE agent on their laptop (no friction)

**README Section:**
```markdown
## Quick Start (Recommended)
Works on any system with 8GB+ RAM:
```bash
ollama run qwen2.5:7b
python src/agent.py
```

## Full Capability Demo (24GB+ RAM)
To see the agent's reasoning process:
```bash
ollama run qwen3.8:27b
python src/agent.py
```
```

### **Layer 2: YouTube Showcase (Recruiter-Viewed, Not Executed)**
**Model:** `Qwen 3.8-27B`
- You record demo with visible thinking process
- 15-minute walkthrough: Query → Thinking → Tool Call → Result
- High production value (pause, explain, annotate)
- Link in README: "Watch the full capability demo"

**Video Structure:**
```
[0:00-1:00]   Intro: "Here's the SRE Agent solving a real incident"
[1:00-3:00]   User query: "SWIFT API timing out"
[3:00-5:00]   LLM thinking process (VISIBLE) ← Qwen 3.8 advantage
[5:00-7:00]   Tool call interception (show JSON schema)
[7:00-9:00]   ChromaDB retrieval (INCIDENT-001 runbook)
[9:00-12:00]  Final response with troubleshooting steps
[12:00-14:00] Performance stats & model comparison
[14:00-15:00] Outro: "Code on GitHub runs Qwen 2.5. 
               This video demo uses Qwen 3.8 for thinking visualization."
```

---

## 💡 **Why This Strategy is Brilliant**

### For Recruiters
| What Happens | Result |
|--------------|--------|
| Clone repo & run | ✅ Works immediately (Qwen 2.5-7B) |
| See tool calling demo | ✅ Proves core skill |
| Watch YouTube | ✅ Impressed by thinking process |
| 15 min engagement | ✅ Full project demo without friction |

### For You (Interview Story)
When asked "Why two models?", explain:

> *"I deploy Qwen 2.5-7B in the portfolio because I want you to actually clone and test it on your laptop in 5 minutes without friction. The video showcases Qwen 3.8's thinking process, demonstrating the full agentic reasoning capability. This mirrors production decisions: smaller models for broad accessibility, larger models for specialized demonstration. Tool calling is JSON-based and works identically on both — the difference is narrative and thinking visualization."*

**This shows:**
- ✅ Pragmatic deployment thinking
- ✅ User experience awareness
- ✅ Production-grade tradeoff reasoning
- ✅ Technical depth (you understand tool calling independent of thinking)

---

## ✅ **Implementation Checklist**

### Phase 3 (Implementation)
- [ ] Code agent loop with Qwen 2.5-7B as default
- [ ] Test tool calling, ChromaDB, error handling
- [ ] Confirm responsive UX (1-2s per query)
- [ ] Document model selection in README

### Phase 4 (Portfolio Polish)
- [ ] Record YouTube video with Qwen 3.8-27B
  - [ ] Set up recording environment (home setup OK)
  - [ ] Script walkthrough: incident query → runbook retrieval
  - [ ] Capture thinking process (pause to explain)
  - [ ] Show final response synthesis
  - [ ] Add captions/annotations
- [ ] Link video in README: "Watch the full capability demo"

### Phase 5 (Final Polish)
- [ ] Add hardware requirements section to README
- [ ] Benchmark performance (Qwen 2.5 vs 3.8 inference time)
- [ ] Consider Nemotron-3.5-L as "production alternative" footnote
- [ ] Add model selection decision link to PROJECT_GUIDE.md

---

## 🎬 **Why YouTube Video at Home Works**

You don't need a fancy setup:
- ✅ Screen recording (built-in Windows/Mac)
- ✅ Terminal + browser (show agent responding)
- ✅ Annotate decisions (add text overlays)
- ✅ 15-20 minutes is plenty (no need for Hollywood production)

Recruiters **value authenticity** over polish. Genuine walkthrough > slick but distant video.

---

## 📋 **Tool Calling Works Identically on Both Models**

**Critical:** Tool calling is JSON-based, not reasoning-based.

```python
# This code works the SAME on Qwen 2.5-7B and Qwen 3.8-27B
response = ollama.chat(model=MODEL, messages=..., tools=[search_runbooks_schema])

if response.message.tool_calls:
    for tool_call in response.message.tool_calls:
        result = search_runbooks(tool_call.function.arguments["query"])
        # Inject result back into context
```

**The difference is UX:**
- Qwen 2.5-7B: Tool calls executed, results returned, response generated (no visible thinking)
- Qwen 3.8-27B: Same flow, PLUS visible reasoning process (impressive for video)

---

## 🎯 **Final Recommendation**

**Ship:** Qwen 2.5-7B (GitHub, recruiter-runnable)  
**Showcase:** Qwen 3.8-27B (YouTube, thinking-visible)  
**Production Alternative:** Nemotron-3.5-L (if throughput matters)

**Status:** ✅ **APPROVED** — Ready for Phase 3 implementation with Qwen 2.5-7B.
