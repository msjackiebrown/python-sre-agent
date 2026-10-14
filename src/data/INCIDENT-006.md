---
id: INCIDENT-006
title: High CPU Usage / Service Consuming 100% CPU
severity: high
keywords: "cpu high usage 100% hot loop spin performance runaway algorithm slowquery missing-index"
contact: app-team-oncall@team.slack.com
escalate: Page Principal Engineer after 15min if CPU remains > 80%; Page VP Engineering after 30min
---

## Description

Process is consuming 100% or near-100% CPU, causing:
- Request timeouts
- Service slowdown
- Cascading failures in dependent services
- System overload

Common causes: O(n²) algorithm, infinite loop, missing database index, N+1 queries, regex DoS, unoptimized calculation.

**Impact:**
- Severe latency increase (p99 spikes to 10+ seconds)
- Service unresponsiveness
- Cascading timeouts to dependent services
- Potential complete service unavailability

## Detection

### Alert Triggers
- `node_cpu_usage_percent > 95` for > 5 minutes
- Alert: `ServiceCPUSpikeAlert` (container CPU > 80% of limit)
- Application metrics: response time spike, request queue growing
- User reports: "service very slow"

### Manual Verification
```bash
# Check system CPU usage
top -b -n 1 | head -15
# Look for processes with high %CPU column

# If Kubernetes
kubectl top pod -n production | sort -k3 -rn
# Shows CPU usage by pod

# Check container limits
kubectl describe pod <pod-name> -n production | grep -A 5 "resources"
```

## Investigation

### Step 1: Identify CPU Hog (1 min)
```bash
# Which process is consuming CPU?
top -u app-user -o %CPU
# or
ps aux | sort -k3 -r | head

# If Kubernetes pod
kubectl top pods -n production | sort -k3 -rn
# If cpu >= limit * 0.95, pod is CPU-bound
```

### Step 2: Understand What It's Doing (2-3 min)
```bash
# Get stack trace (if Go)
curl http://localhost:6060/debug/pprof/profile?seconds=30 > /tmp/cpu.prof
go tool pprof /tmp/cpu.prof
(pprof) top10 -cum

# If Java
jstack <pid> > /tmp/stack.txt
cat /tmp/stack.txt | head -50
# Look for: "runnable" threads, "waiting" threads (deadlock?)

# If Python
python -m cProfile -s cumulative /path/to/app.py
```

### Step 3: Check for Known Causes (1-2 min)
```bash
# Recent deployment?
kubectl rollout history deployment/api-server

# Query performance?
# Check slow query log
tail -50 /var/log/mysql/slow-query.log

# Show most expensive queries
pt-query-digest /var/log/mysql/slow-query.log --review

# Check request volume spike
curl 'https://prometheus.internal/api/v1/query?query=rate(http_requests_total[1m])'
# If requests_per_second increased 10x, that might be the cause (legitimately busy)
```

## Remediation

### Phase 1: IMMEDIATE (0-2 min) - Relieve Pressure

**Option A: Gracefully Restart Service**
```bash
# If service is stuck in infinite loop/bad state
kubectl -n production rollout restart deployment/api-server
# Sends SIGTERM (graceful), waits terminationGracePeriodSeconds (default 30s)

# Monitor restart
kubectl -n production rollout status deployment/api-server
```

**Option B: Scale Down Temporarily**
```bash
# If CPU spike due to legitimate high load
kubectl -n production scale deployment api-server --replicas=1
# Reduces number of processes, easier to debug

# Monitor if CPU drops
watch -n 2 'kubectl top pod -n production -l app=api-server'
```

**Option C: Kill Specific Process (Last Resort)**
```bash
# If graceful restart fails
kubectl -n production exec -it <pod-name> -- kill -9 <pid>
# or
kubectl -n production delete pod <pod-name>
# (Kubernetes will restart it via ReplicaSet)
```

### Phase 2: ROOT CAUSE INVESTIGATION (2-5 min)

**If Recent Deployment - Check Code Changes**
```bash
git log --oneline -10
git diff HEAD~1 HEAD

# Look for:
# - New loop iteration without break/continue
# - Missing index() call before filter/search
# - Regex without anchors (catastrophic backtracking)
# - N+1 database queries
# - Removed early-exit condition

# Rollback if suspected
kubectl -n production rollout undo deployment/api-server --to-revision=<previous>
```

**If Slow Query (Database)**
```bash
# Get top slow queries
mysql> SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 10\\G

# Analyze query
mysql> EXPLAIN SELECT ... FROM ...;
# Look for: full table scan (type=ALL), or many rows examined

# Example: Missing index
# EXPLAIN shows: rows=1000000 examined for simple lookup
# Fix: CREATE INDEX idx_user_id ON users(id);

mysql> CREATE INDEX idx_lookup ON table_name(column_name);
mysql> ANALYZE TABLE table_name;
```

**If N+1 Query Problem**
```java
// BEFORE (N+1 problem - queries database N times in loop)
List<User> users = userRepository.findAll();
for (User user : users) {
    List<Orders> orders = orderRepository.findByUserId(user.getId());  // N queries!
    user.setOrders(orders);
}

// AFTER (single query with join/fetch)
List<User> users = userRepository.findAllWithOrders();  // JPQL: JOIN FETCH
// Or batch:
List<Integer> userIds = users.stream().map(User::getId).collect(toList());
Map<Integer, List<Order>> ordersByUser = orderRepository.findByUserIdIn(userIds)
    .stream()
    .collect(groupingBy(Order::getUserId));
```

**If Infinite Loop / Deadlock**
```go
// BEFORE (possible infinite loop)
for {
    result := process()
    if result.Done {
        break
    }
    // missing break condition or infinite recursion
}

// AFTER (safe loop with timeout)
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()

for {
    select {
    case <-ctx.Done():
        return ctx.Err()  // exit after 30 seconds
    default:
        result := process()
        if result.Done {
            break
        }
    }
}
```

**If Algorithm Complexity Issue**
```python
# BEFORE - O(n²) nested loops
def find_duplicates(items):
    for i in range(len(items)):
        for j in range(i+1, len(items)):  # re-scans whole list
            if items[i] == items[j]:
                return items[i]
    return None

# AFTER - O(n) with hash set
def find_duplicates(items):
    seen = set()
    for item in items:
        if item in seen:  # O(1) lookup
            return item
        seen.add(item)
    return None
```

### Phase 3: DEPLOY FIX

```bash
# Commit fix
git commit -m "[FIX] CPU spike: add missing database index on user_id"
git push

# Deploy
kubectl -n production set image deployment/api-server api-server=company/api-server:v1.2.3
kubectl -n production rollout status deployment/api-server

# Monitor CPU dropping
watch -n 5 'kubectl top pod -n production -l app=api-server'
# Should see CPU drop from 95%+ → 10-20% normal range
```

## Validation

### Success Criteria
- [ ] CPU usage drops below 20% (normal range)
- [ ] p99 latency drops from 10s+ → < 500ms
- [ ] No errors in logs
- [ ] Request processing rate stabilizes
- [ ] Service responds normally to requests

```bash
# Monitor CPU over time
kubectl top pod -n production -l app=api-server
kubectl top node  # overall node health

# Query performance metrics
curl 'https://prometheus.internal/api/v1/query?query=rate(http_requests_total[1m])'
curl 'https://prometheus.internal/api/v1/query?query=histogram_quantile(0.99, http_request_duration_seconds)'
# p99 should be < 0.5 seconds
```

## Escalation

- **0-2 min:** Page app-team-oncall@team.slack.com
- **2-5 min:** Identify root cause
- **5-15 min:** If CPU still > 80%, page Principal Engineer
- **15-30 min:** If not resolved, page VP Engineering
- **30+ min:** CEO-level incident (service down)

## Contacts & Resources

- **Slack:** #application-incidents
- **PagerDuty:** app-primary, principal-engineer
- **Performance Tools:**
  - Go pprof: `curl http://localhost:6060/debug/pprof/profile?seconds=30`
  - Java jstack: `jstack <pid>`
  - Python cProfile: `python -m cProfile`
  - Linux perf: `perf record` + `perf report`
- **References:** https://brendangregg.com/linuxperf.html