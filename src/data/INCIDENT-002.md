---
id: INCIDENT-002
title: Service Returns 5xx Errors (500, 502, 503, 504)
severity: critical
keywords: "error 5xx 500 502 503 504 service down unavailable crash panic outage unhealthy"
contact: platform-oncall@team.slack.com
escalate: Page SRE Manager after 2min; Page VP Engineering after 5min
---

## Description

Service is returning HTTP 5xx errors indicating service crash, dependency failure, or resource exhaustion. Complete user-facing outage with potential cascading failures.

## Detection

### Alert Triggers
- `http_requests_5xx_total` spike from 0 → 1000s per minute
- Error rate > 1% (or > 0.1% for critical services)
- Uptime monitoring: All /health checks failing

### Manual Verification
```bash
# Check service health
curl -v https://api-prod.internal/health 2>&1 | head -20

# Check pod status
kubectl -n production get pods -l app=api-prod -o wide

# Check recent logs for panic
kubectl -n production logs -l app=api-prod --tail=100 | grep -i panic
```

## Investigation

### Step 1: Determine Scope (0-1 min)
```bash
# Are ALL replicas failing or just some?
kubectl -n production get deployment api-prod

# Check pod status
kubectl -n production describe pod -l app=api-prod | grep -A 5 'Last State'
# Look for: "Exit Code: 1" or "OOMKilled" or "CrashLoopBackOff"

# Recent deployment?
kubectl -n production rollout history deployment/api-prod
```

### Step 2: Check Dependencies (1-2 min)
```bash
# Is database reachable?
kubectl -n production run -it --rm debug --image=busybox -- nc -zv prod-db-01.us-east-1.aws 3306

# Is Redis up?
redis-cli -h prod-redis-01.us-east-1.aws -p 6379 ping

# Check upstream service
curl -v https://upstream-service.internal/health
```

### Step 3: Analyze Logs (2-3 min)
```bash
# Get logs from recent crashes
kubectl -n production logs -l app=api-prod --tail=500 --previous

# Look for patterns: panic, oom, connection refused, timeout

# Count error types
kubectl -n production logs -l app=api-prod --tail=1000 | grep ERROR | head -20
```

## Remediation

### Phase 1: STOP THE BLEEDING (0-2 min)

**Rollback to Last Known Good**
```bash
kubectl -n production rollout history deployment/api-prod
kubectl -n production rollout undo deployment/api-prod --to-revision=41
kubectl -n production rollout status deployment/api-prod
```

**Or Scale Down & Restart**
```bash
kubectl -n production scale deployment api-prod --replicas=0
sleep 10
kubectl -n production scale deployment api-prod --replicas=3
kubectl -n production rollout status deployment/api-prod
```

### Phase 2: ROOT CAUSE FIX (2-5 min)

**If OOMKilled:**
```bash
kubectl -n production set resources deployment api-prod --limits=memory=3Gi
```

**If Database Connection Issue:**
```bash
mysql -h prod-db-01.us-east-1.aws -u app-user -p${DB_PASSWORD} -e "SELECT 1;"
mysql -e "SHOW STATUS LIKE 'Threads%';"
```

**If Recently Deployed:**
```bash
git revert <commit-hash>
git push
# CI/CD auto-deploys or manually trigger
```

## Validation

### Success Criteria
- [ ] All pods status: Running
- [ ] `curl /health` returns 200 OK
- [ ] Error rate (5xx) drops to < 0.1%
- [ ] p99 latency < 500ms
- [ ] No goroutine growth over 5 minutes

```bash
kubectl -n production rollout status deployment/api-prod
kubectl -n production get pods -l app=api-prod
curl -s https://api-prod.internal/health | jq '.'
```

## Escalation

- **0-2 min:** Page platform-oncall@team.slack.com
- **2-5 min:** Page SRE Manager
- **5+ min:** Page VP Engineering

## Contacts & Resources

- **Slack:** #production-incidents
- **PagerDuty:** sre-primary
- **Dashboards:** https://grafana.internal/d/api-prod-health
- **Status:** https://status.internal/