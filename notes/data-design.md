---
title: Data Design - Runbook Schema & ChromaDB Storage
subject: Phase 2 - Data Ingestion Design Document
date: 2026-10-14
tags: [data-design, runbook-schema, chromadb, phase-2]
status: Active Design
---

# 📊 Data Design: Runbook Schema & ChromaDB Structure

**Phase:** 2 (Data Ingestion)  
**Status:** Design & Planning  
**Deliverable:** `src/data/INCIDENT-*.md` + `src/runbook_db.py`

---

## 1. What is a Runbook?

**Definition:** An executable playbook for responding to a known incident pattern.

**Our context (SRE Agent):**
- Help on-call engineers quickly find and execute known incident responses
- Real-world examples: Database timeouts, service crashes, memory leaks, API rate limits
- Goal: LLM says "Try this" → Engineer finds step-by-step runbook → Incident resolved faster

---

## 2. Runbook Schema (Data Structure)

### Top-Level Fields

```
INCIDENT-001.md
├── Title (string)         - "Database Connection Timeout"
├── Keywords (string)      - Searchable tags/phrases
├── Steps (array)          - Ordered remediation steps
├── Contact (string)       - Who to page/Slack
├── Escalate (string)      - Escalation criteria & who to page
└── Severity (enum)        - "critical", "high", "medium", "low"
```

### Field Details

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| **Title** | string | Display name for runbook | "Database Connection Timeout" |
| **Keywords** | string | Space-separated search terms | "timeout database connection pool peak load" |
| **Steps** | array[string] | Numbered remediation actions | ["Check pool status", "Increase max_connections", ...] |
| **Contact** | string | Primary on-call | "db-oncall@team.slack.com" |
| **Escalate** | string | When & who to escalate | "Page DB lead after 15min if not resolved" |
| **Severity** | enum | Priority level | "high" |

---

## 3. Runbook Markdown Format

### File Structure

Each runbook is a Markdown file with frontmatter + content:

```markdown
---
id: INCIDENT-001
title: Database Connection Timeout
severity: high
keywords: timeout database connection pool peak load latency
contact: db-oncall@team.slack.com
escalate: Page Platform Lead after 15min if not resolved
---

## Description
Occurs when the database connection pool is exhausted and new connections are refused. Common during traffic spikes or memory leaks in client connections.

## Detection
- Application logs: "Connection pool exhausted"
- Metrics: `db.pool.connections.used` == `db.pool.connections.max`
- Alert: `DatabasePoolUtilizationAlert` fires

## Investigation
1. SSH to database primary: `ssh prod-db-01.aws`
2. Check pool status: `mysql> SHOW STATUS LIKE 'Threads%';`
3. Query slow queries: `mysql> SHOW FULL PROCESSLIST;`
4. Review application connection string

## Remediation
1. **Immediate (0-2min):** Increase max_connections
   - `mysql> SET GLOBAL max_connections = 5000;`
   - Verify: `SHOW VARIABLES LIKE 'max_connections';`

2. **Short-term (2-10min):** Identify connection leak in app
   - Check connection timeout settings in driver
   - Look for unclosed connections in application logs
   - Restart affected microservice: `kubectl rollout restart deployment/api`

3. **Long-term (after incident):** Implement connection pooling proxy
   - Deploy ProxySQL or PgBouncer
   - Set max_connections per service
   - Add monitoring alert for pool utilization > 80%

## Validation
- Metrics return to baseline
- Application logs show no new "Connection pool exhausted" errors
- Database response time < 100ms

## Escalation
- **5min no progress:** Page Platform Engineering Lead
- **10min no progress:** Page Infrastructure Manager
- **15min no progress:** Wake up DB Principal Architect

## Contacts
- **Slack:** #database-incidents
- **PagerDuty:** db-primary
- **Runbook:** https://wiki.internal/runbooks/database-timeout
```

---

## 4. Example Runbooks (7 Incidents)

### INCIDENT-001: Database Connection Timeout
```yaml
id: INCIDENT-001
title: Database Connection Timeout
severity: high
keywords: "timeout database connection pool peak load latency exhausted refused max_connections"
contact: db-oncall@team.slack.com
escalate: Page DB Lead after 15min if not resolved
```

### INCIDENT-002: Service 5xx Errors
```yaml
id: INCIDENT-002
title: Service 5xx Errors (500, 502, 503)
severity: critical
keywords: "error 5xx 500 502 503 service down unavailable panic crash"
contact: platform-oncall@team.slack.com
escalate: Page SRE Manager after 5min if not resolved
```

### INCIDENT-003: Memory Leak in Worker Process
```yaml
id: INCIDENT-003
title: Memory Leak in Worker Process
severity: high
keywords: "memory leak oom out-of-memory worker process heap goroutine leak"
contact: app-oncall@team.slack.com
escalate: Page Engineering Manager after 20min if not resolved
```

### INCIDENT-004: API Rate Limit Exceeded
```yaml
id: INCIDENT-004
title: API Rate Limit Exceeded
severity: medium
keywords: "rate limit 429 throttle api quota exceeded backoff"
contact: api-oncall@team.slack.com
escalate: Page API Team Lead after 10min if not resolved
```

### INCIDENT-005: Disk Space Critical
```yaml
id: INCIDENT-005
title: Disk Space Critical (>95% utilized)
severity: high
keywords: "disk space filesystem full df -h inode volume storage"
contact: infrastructure-oncall@team.slack.com
escalate: Page Infrastructure Lead after 5min if not resolved
```

### INCIDENT-006: Service Dependency Timeout
```yaml
id: INCIDENT-006
title: Service Dependency Timeout (Downstream Service)
severity: high
keywords: "timeout dependency downstream service call circuit breaker timeout"
contact: platform-oncall@team.slack.com
escalate: Page affected service owner after 5min if not resolved
```

### INCIDENT-007: Certificate Expiration
```yaml
id: INCIDENT-007
title: TLS Certificate Expiration
severity: critical
keywords: "certificate tls ssl expired expiration x509 renewal"
contact: security-oncall@team.slack.com
escalate: Page Security Lead immediately, Page DevOps after 2min if not resolved
```

---

## 5. How Runbooks Map to ChromaDB

### Storage Strategy

```python
# Phase 2: Seed runbooks into ChromaDB

runbooks = [
    {
        "id": "INCIDENT-001",
        "title": "Database Connection Timeout",
        "keywords": "timeout database connection pool peak load latency exhausted refused max_connections",
        "full_content": "[Full markdown from above]",
        "contact": "db-oncall@team.slack.com",
        "escalate": "Page DB Lead after 15min if not resolved",
        "severity": "high"
    },
    # ... 6 more runbooks ...
]

# What goes WHERE in ChromaDB?
collection.add(
    ids=[r["id"] for r in runbooks],
    
    # SEARCH ON: keywords + title (for semantic search)
    documents=[f"{r['title']} {r['keywords']}" for r in runbooks],
    
    # RETURN WITH: all metadata needed for display
    metadatas=[{
        "title": r["title"],
        "contact": r["contact"],
        "escalate": r["escalate"],
        "severity": r["severity"],
        "full_content": r["full_content"]  # Full runbook text
    } for r in runbooks]
)
```

### Query Flow

```
User Query: "database is slow and timing out"
        ↓
ChromaDB Semantic Search (on keywords + title)
        ↓
Find: INCIDENT-001 (Database Connection Timeout) - distance: 0.12 (good match!)
        ↓
Return: {
    "id": "INCIDENT-001",
    "title": "Database Connection Timeout",
    "contact": "db-oncall@team.slack.com",
    "escalate": "Page DB Lead after 15min",
    "full_content": "[Full markdown steps...]"
}
        ↓
Agent says: "This looks like INCIDENT-001. Here are the steps..."
        ↓
On-call engineer follows runbook → Incident resolved!
```

---

## 6. Data Ingestion Strategy (Phase 2)

### Step 1: Create Markdown Files
```
src/data/
├── INCIDENT-001.md
├── INCIDENT-002.md
├── ...
└── INCIDENT-007.md
```

### Step 2: Create RunbookDatabase Class
```python
# src/runbook_db.py

import chromadb
from pathlib import Path

class RunbookDatabase:
    def __init__(self):
        """Initialize ChromaDB in-memory and seed runbooks."""
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name="runbooks",
            metadata={"hnsw:space": "cosine"}
        )
        self._seed_runbooks()
    
    def _seed_runbooks(self):
        """Load all INCIDENT-*.md files and add to ChromaDB."""
        data_dir = Path(__file__).parent / "data"
        runbook_files = sorted(data_dir.glob("INCIDENT-*.md"))
        
        for file_path in runbook_files:
            # Parse markdown + frontmatter
            # Extract: id, title, keywords, contact, escalate, severity, content
            # Add to collection
            pass
    
    def search(self, query: str, max_results: int = 5) -> list:
        """Search runbooks by semantic similarity."""
        results = self.collection.query(
            query_texts=[query],
            n_results=max_results
        )
        # Format and return results
        return results
```

### Step 3: Test
```bash
python src/runbook_db.py
# Output: ✅ Seeded 7 runbooks
# 📋 Database Connection Timeout
# 📋 Service 5xx Errors
# [... etc ...]
```

---

## 7. Design Decisions & Rationale

### Q: Why keywords as space-separated string?

**Answer:** ChromaDB converts documents to vectors. Keywords help semantic similarity:
- ✅ "pool timeout database" → finds connection timeout incidents
- ✅ Can add acronyms: "oom out-of-memory memory leak"
- ✅ Easy to expand without schema changes

### Q: Why store full markdown in metadata?

**Answer:** LLM needs complete runbook text to give accurate advice:
- ✅ Agent can cite exact steps
- ✅ Full context available for follow-up questions
- ✅ No second database lookup needed

### Q: Why severity field if not searched on?

**Answer:** Future extensibility:
- ✅ UI can highlight critical incidents
- ✅ Agent can prioritize by severity
- ✅ Metrics can track by severity

### Q: Why cosine similarity and not other metrics?

**Answer:** Cosine is standard for text embeddings:
- ✅ Ignores document length (shorter keywords don't lose)
- ✅ Measures angle between vectors (semantic meaning)
- ✅ Works well with all-MiniLM embeddings (default)

---

## 8. File Structure (Phase 2 Deliverables)

```
src/
├── agent.py           (empty, Phase 4)
├── tools.py           (empty, Phase 3)
├── runbook_db.py      ← CREATE THIS (Phase 2)
└── data/
    ├── INCIDENT-001.md  ← CREATE THESE (Phase 2)
    ├── INCIDENT-002.md
    ├── INCIDENT-003.md
    ├── INCIDENT-004.md
    ├── INCIDENT-005.md
    ├── INCIDENT-006.md
    └── INCIDENT-007.md
```

---

## 9. Test Proof (Phase 2 Success Criteria)

✅ `python src/runbook_db.py` runs without errors  
✅ Outputs "✅ Seeded 7 runbooks"  
✅ `search("database timeout")` returns INCIDENT-001 as top result  
✅ `search("5xx error")` returns INCIDENT-002 as top result  
✅ All 7 incidents searchable and relevant  

---

## 10. Next Steps

1. **Now (Session):** Agree on this schema
2. **Next:** Create 7 INCIDENT-*.md files in `src/data/`
3. **Then:** Create `src/runbook_db.py` with RunbookDatabase class
4. **Then:** Run `python src/runbook_db.py` to verify
5. **Then:** Phase 3 (Tools with Pydantic validation)
