---
id: INCIDENT-001
title: Database Connection Timeout During Peak Load
severity: high
keywords: "timeout database connection pool peak load latency exhausted refused max_connections blocked idle"
contact: db-oncall@team.slack.com
escalate: Page Database Platform Lead after 15min if not resolved; Page Infrastructure VP after 30min
---

## Description

Occurs when the database connection pool is exhausted and new connections are refused. This typically happens during traffic spikes, application memory leaks causing unclosed connections, or inefficient connection pooling configuration. Common in production microservice architectures with many client applications.

**Impact:**
- Application receives "connection refused" errors
- User-facing requests timeout (typically 30-60s)
- Cascading failures as dependent services also timeout

## Detection

### Alert Triggers
- `mysql> SHOW STATUS LIKE 'Threads%';` → Threads_connected ≈ max_connections
- CloudWatch: `db.pool.connections.used` / `db.pool.connections.max` > 0.85
- Application logs: `ERROR: java.sql.SQLException: Cannot get a connection, pool error`
- Monitoring: `database.connection.pool.utilization_percent > 80`

### Manual Verification
```bash
# SSH to database primary
ssh prod-db-01.us-east-1.aws

# Check pool status
mysql -u root -p${DB_PASSWORD} -e "SHOW STATUS LIKE 'Threads%'; SHOW VARIABLES LIKE 'max_connections';"

# Expected output:
# Threads_connected:   4980  (should be << max_connections)
# max_connections:     5000
# If Threads_connected ≥ 4800, we're in danger zone
```

## Investigation

### Step 1: Assess Current Severity (Immediately)
```bash
# Check active connections and their age
mysql> SELECT ID, USER, HOST, COMMAND, TIME, STATE, INFO 
       FROM INFORMATION_SCHEMA.PROCESSLIST 
       WHERE COMMAND != 'Sleep' AND TIME > 300 
       ORDER BY TIME DESC LIMIT 10;
```

### Step 2: Identify Connection Leaks (2-5 min)
```bash
# Top applications by connection count
mysql> SELECT USER, HOST, COUNT(*) as connections 
       FROM INFORMATION_SCHEMA.PROCESSLIST 
       GROUP BY USER, HOST 
       ORDER BY connections DESC;
```

### Step 3: Check Slow Query Log (2-3 min)
```bash
# Identify long-running transactions
mysql> SELECT * FROM INFORMATION_SCHEMA.INNODB_LOCKS;
mysql> SHOW FULL PROCESSLIST WHERE COMMAND != 'Sleep' LIMIT 20;
```

## Remediation

### Phase 1: Immediate (0-2 min)
```bash
mysql> SET GLOBAL max_connections = 6000;  # increase by 20%
mysql> FLUSH PRIVILEGES;

# Verify
mysql> SHOW VARIABLES LIKE 'max_connections';
```

### Phase 2: Short-term (2-10 min)
```bash
# Restart the leaky application
kubectl -n production rollout restart deployment/api-prod
kubectl -n production rollout status deployment/api-prod
```

## Validation

### Success Criteria
- [ ] Threads_connected < 500
- [ ] Connection pool < 50% utilization
- [ ] No "connection refused" errors
- [ ] p99_latency < 500ms

```bash
mysql> SHOW STATUS LIKE 'Threads%';
curl -s https://api-prod.internal/health | jq '.database.pool'
```

## Escalation

- **0-5 min:** Page db-oncall@team.slack.com (#database-incidents)
- **5-10 min:** Page Database Platform Lead (PagerDuty: `db-lead-primary`)
- **15+ min:** Page VP Engineering

## Contacts & Resources

- **Slack:** #database-incidents
- **PagerDuty:** db-primary
- **Dashboard:** https://grafana.internal/d/db-connections