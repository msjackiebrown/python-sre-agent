---
id: INCIDENT-003
title: Memory Leak in Worker Process (Goroutine/Heap Leak)
severity: high
keywords: "memory leak oom out-of-memory worker process heap goroutine leak growth unbounded retained"
contact: app-oncall@team.slack.com
escalate: Page Engineering Lead after 20min; Page Backend Platform Lead after 40min
---

## Description

Long-running worker process continuously accumulating memory without release. Indicates memory leak in application code. Common causes: goroutine leaks, circular references, unbounded cache, resource not freed, slice reallocation.

**Impact:**
- Worker memory grows to 90-100% of limit
- Process killed by OOMKiller
- Worker jobs fail or take longer
- Cascading delays in batch pipeline
- Complete worker unavailability

## Detection

### Alert Triggers
- `container_memory_usage_bytes` growing > 50MB/min consistently
- Memory reaching > 85% of pod limit
- Alert: `WorkerMemoryLeakAlert` (memory > limit for > 5 min)
- Restart counter increasing (`RESTARTS` column > 1)

### Manual Verification
```bash
# Check current memory usage
kubectl -n production top pods -l app=worker-batch

# Watch memory over time
watch -n 5 'kubectl -n production top pods -l app=worker-batch'

# Check restart count
kubectl -n production get pods -l app=worker-batch
```

## Investigation

### Step 1: Confirm Leak Pattern (1-2 min)
```bash
# Get memory history
kubectl -n production exec -it worker-batch-abc123 -- curl http://localhost:8080/metrics | grep 'go_memstats_heap_alloc_bytes' | tail -20
```

### Step 2: Identify Leak Source (2-5 min)
```bash
# Get detailed heap dump
kubectl -n production exec -it worker-batch-abc123 -- curl http://localhost:6060/debug/pprof/heap > /tmp/heap.prof

# Analyze with pprof
go tool pprof /tmp/heap.prof
```

### Step 3: Check Goroutine Count (1-2 min)
```bash
# Get goroutine profile
kubectl -n production exec -it worker-batch-abc123 -- curl http://localhost:6060/debug/pprof/goroutine?debug=2 > /tmp/goroutines.txt

# Count goroutines (should be < 500 for worker)
grep 'goroutine ' /tmp/goroutines.txt | head -1
```

## Remediation

### Phase 1: STOP THE BLEEDING (Immediate)

**Restart the Worker**
```bash
kubectl -n production rollout restart deployment/worker-batch
kubectl -n production rollout status deployment/worker-batch
# Memory should drop from 2200Mi → 300Mi
```

### Phase 2: Implement Temporary Fix (5-10 min)

**Add Graceful Restart Policy**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-batch
spec:
  template:
    spec:
      env:
      - name: RESTART_INTERVAL_HOURS
        value: "24"
      restartPolicy: Always
```

### Phase 3: ROOT CAUSE FIX (Engineering Task)

**Goroutine Leak Pattern:**
```go
// BEFORE - goroutine never exits
// AFTER - add context cancellation
func (w *Worker) processJobs(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return
        case job := w.queue.Fetch(ctx):
            go w.handleJob(ctx, job)
        }
    }
}
```

**Unbounded Cache Pattern:**
```go
// Add TTL and max size to cache
type Cache struct {
    data map[string]*CacheEntry
    maxSize int
    ttl time.Duration
}
```

## Validation

### Success Criteria
- [ ] Memory stable (not growing) over 1+ hour
- [ ] Goroutine count stable (< 200 for worker)
- [ ] No OOMKilled restarts
- [ ] Job latency back to baseline

## Escalation

- **0-5 min:** Page app-oncall@team.slack.com
- **5-20 min:** Investigate with team
- **20-30 min:** If growing, restart and page Engineering Lead
- **30-40 min:** If still growing, page Backend Platform Lead

## Contacts & Resources

- **Slack:** #backend-incidents
- **PagerDuty:** app-primary
- **Dashboard:** https://grafana.internal/d/worker-memory-profiling