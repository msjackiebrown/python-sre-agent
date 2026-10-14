---
title: Decision - AI-Generated Sample Runbook Data
subject: Python SRE Agent
section: Design Decisions & Documentation
phase: Phase 2 (Design) → Phase 3 (Implementation)
date: 2026-10-13
status: Approved
tags: [runbook-data, testing, mock-data, sample-data, ai-generation]
---

## Decision
**Use AI (GitHub Copilot) to generate sample runbook data for testing and demonstration purposes.**

## Rationale

### 1. Time Efficiency
- **Manual approach:** Research and write 5+ realistic SRE runbooks = 4–6 hours
- **AI-assisted approach:** Define template + review/edit AI output = 1 hour
- **Trade-off:** Acceptable. Sample data doesn't need to be production-perfect; it needs to be *representative* and *searchable*

### 2. Representative Coverage
- **Scope:** Choose diverse incident types to test semantic search across domains
  - Database issues (INCIDENT-001: Timeout)
  - Service health (INCIDENT-002: 5xx Errors)
  - Infrastructure (INCIDENT-003: Memory Leak, INCIDENT-004: Certificates, INCIDENT-005: Disk Full)
  - Performance (INCIDENT-006: CPU Spike)
  - Networking (INCIDENT-007: Connectivity)
- **Benefit:** ChromaDB vector search can be tested against varied incident contexts

### 3. Similarity to Real Enterprise SRE Workflows
- **Authenticity:** AI was trained on real documentation (Kubernetes docs, Linux troubleshooting guides, oncall playbooks)
- **Realism:** Generated runbooks follow industry-standard incident response format (Steps → Contact → Escalation)
- **Caveat:** *Not* based on actual production incidents from our organization (no real PII, no real system names used)

### 4. Iteration & Refinement
- **AI enables fast iteration:** If we discover test gaps, regenerating runbooks is faster than writing manually
- **Example:** If agent fails to invoke search tool for a certain query pattern, we can quickly add a runbook with that exact keyword

### 5. Legal & Compliance
- **No sensitive data:** All mock runbooks use generic names (INCIDENT-001, etc.) and fictional company names
- **No trade secrets:** Runbooks follow public SRE best practices (Linux troubleshooting, Kubernetes management), not proprietary workflows
- **Disclaimer:** Marked as "FAKE" or "Sample" in repository context (via folder name `src/data/` and README)

---

## Decision Documentation

### Runbooks Generated (Phase 2)
- **INCIDENT-001:** Database Connection Timeout (manual)
- **INCIDENT-002:** Service 5xx Errors (manual)
- **INCIDENT-003:** Memory Leak / OOM (AI-generated, reviewed)
- **INCIDENT-004:** Certificate Expiration / SSL (AI-generated, reviewed)
- **INCIDENT-005:** Disk Space Critical (AI-generated, reviewed)
- **INCIDENT-006:** High CPU Usage (AI-generated, reviewed)
- **INCIDENT-007:** Network Connectivity (AI-generated, reviewed)

### Quality Assurance Process
Each AI-generated runbook was reviewed for:
1. **Correctness:** Commands are valid Linux/Kubernetes operations
2. **Realism:** Steps follow actual SRE incident response workflows
3. **Consistency:** Format matches existing runbooks (INCIDENT-001, INCIDENT-002)
4. **Searchability:** Keywords align with expected user queries ("incident", "error", "timeout", "certificate", etc.)

### Future Iterations (Phase 3+)
- If testing reveals ChromaDB fails to match certain query patterns, add targeted runbooks
- If agent behavior testing requires new incident types, regenerate runbooks as needed
- Plan to migrate to *real* organization runbooks in Phase 5 (if available for portfolio review)

---

## Alternative Approaches Considered

| Approach | Pros | Cons | Decision |
| --- | --- | --- | --- |
| **Manual writing** | Full control, guaranteed accuracy | 4–6 hours overhead | ❌ Rejected |
| **Copy from real incidents** | Authentic, real-world tested | PII risk, legal complexity | ❌ Rejected |
| **AI-generated (chosen)** | Fast, representative, editable | Requires review, may contain hallucinations | ✅ Approved |
| **Public SRE playbooks** | Real-world, well-reviewed | Limited variety, not all transferable | ⚠️ Consider Phase 5 |

---

## Transparency & Disclosure
- Repository README must clearly state: "Mock runbook data generated for demonstration purposes"
- In Phase 5, if publishing project (portfolio), add disclaimer: "Sample data created with AI assistance for testing; not based on real incidents"
- No claim that this represents actual organizational incident response (it's a chatbot testing framework)

---

## Related Decisions
- **Tool Description Precision** – Runbook keywords must match Golden Description trigger conditions (see sre-agent-runbook-search.md)
- **ChromaDB Seeding Strategy** – All 7 runbooks bulk-loaded at startup into in-memory ChromaDB (see llm-chatbot-reference.md)

---

## Metrics for Success (Phase 3 Testing)
- [ ] Agent successfully searches and retrieves relevant runbook for "database timeout" query
- [ ] Agent skips search tool for "Hello, how are you?" (false positive test)
- [ ] Agent retrieves 3+ different runbook types across test suite (coverage test)
- [ ] Semantic search latency < 100ms per query (performance baseline)

---

## References
- [Runbook Implementation](./sre-agent-runbook-search.md)
- [Tool Calling Design](./tool-calling.md)
- [Startup Checklist](./llm-chatbot-reference.md#startup-checklist-for-sre-agent-phase-3)
