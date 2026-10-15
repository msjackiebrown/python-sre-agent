---
id: INCIDENT-004
title: API Rate Limit Exceeded (HTTP 429 Throttling)
severity: medium
keywords: "rate limit 429 throttle quota exceeded backoff retry client attack ddos traffic spike"
contact: api-oncall@team.slack.com
escalate: Page API Team Lead after 10min; Page Security Team if potential attack
---

## Description

API servers rejecting requests with HTTP 429 (Too Many Requests) because incoming request rate exceeds configured limits. Can be legitimate spike (product launch, viral feature) or malicious attack (DDoS, bot, credential stuffing).

**Impact:**
- Client applications receive 429 responses
- User requests timeout waiting for retry
- Cascading failures if clients don't implement backoff
- Potential revenue loss if too aggressive

## Detection

### Alert Triggers
- `http_requests_429_total` spike from ~0 → 1000s per minute
- Alert: `HighRateLimitRejectionRate` (429 errors > 5% of traffic)
- Alert: `TopClientExceededQuota` (single client > 50% of quota)

### Manual Verification
```bash
# Check current 429 rate
kubectl -n production logs -l app=api-server --tail=1000 | grep '429' | wc -l

# See rate over time
watch -n 5 'curl -s https://prometheus.internal/api/v1/query?query=increase%28http_requests_429_total%5B1m%5D%29'

# Top offenders
kubectl -n production exec -it api-server-abc123 -- redis-cli KEYS "rate_limit:*"
```

## Investigation

### Step 1: Identify Top Offenders (1-2 min)
```bash
# Which clients hitting limits?
kubectl -n production exec -it api-server-abc123 -- redis-cli GET "rate_limit:client_id:customer-123"

# Prometheus query
curl 'https://prometheus.internal/api/v1/query' --data-urlencode 'query=topk(10, rate(http_requests_total[1m]) by (client_id))'
```

### Step 2: Analyze Request Pattern (1-2 min)
```bash
# Requests by endpoint from top client
kubectl -n production logs --tail=5000 | grep 'client_id=customer-123' | cut -d' ' -f10 | sort | uniq -c | sort -rn

# Is it a retry storm?
kubectl -n production logs --tail=10000 | grep 'customer-123' | grep '429' | head -20
```

### Step 3: Determine If Legitimate or Attack (1-2 min)
```bash
# Check request IP and user agent
kubectl -n production logs --tail=5000 | grep 'customer-123' | head -10

# Is it single IP or distributed?
kubectl -n production logs --tail=5000 | grep 'customer-123' | cut -d' ' -f8 | sort | uniq
# 1-2 IPs = likely single client misbehaving
# 100+ IPs = likely distributed attack

# Check if known customer
curl -s https://api.internal/internal/customers/by-id/customer-123 | jq '.'
```

## Remediation

### Phase 1: STOP THE BLEEDING (0-2 min)

**Temporarily Increase Rate Limit**
```bash
kubectl -n production exec -it api-server-abc123 -- redis-cli
> SETEX "rate_limit:override:customer-123" 3600 "50000"

# Or via API
curl -X POST https://api.internal/internal/rate-limits/override -H "X-Admin-Token: ${ADMIN_TOKEN}" -d '{
  "client_id": "customer-123",
  "new_limit": 50000,
  "duration_seconds": 3600,
  "reason": "Legitimate spike"
}'
```

**Block Suspected Attack**
```bash
kubectl -n production exec -it api-server-abc123 -- redis-cli
> SETEX "ip_blocklist:192.168.100.5" 3600 "1"
```

### Phase 2: INVESTIGATE ROOT CAUSE (2-5 min)

**If Legitimate Spike:**
```bash
# Document business context
echo "Rate limit incident:"
echo "Customer: Acme Corp (enterprise tier)"
echo "Reason: Product launch campaign"
echo "Duration: 2 hours"
echo "Action: Increased rate limit from 10k to 50k"

# Notify customer success
slack-notify @customer-success "Rate limit increased for Acme Corp"
```

**If Client Retry Bug:**
```bash
# Identify problematic client version
kubectl -n production logs --tail=10000 | grep 'user_agent' | cut -d'=' -f4 | sort | uniq -c

# Reach out to customer
slack-message @customer-success "CustomClient/2.1 bug detected - needs upgrade to v2.2"
```

**If Attack Suspected:**
```bash
# Alert security
slack-notify @security "Rate limit incident - possible attack"

# Block entire customer
kubectl -n production exec -it api-server-abc123 -- redis-cli
> SETEX "client_blocklist:customer-123" 3600 "1"
```

### Phase 3: IMPLEMENT LONG-TERM FIX

**Client-Side Exponential Backoff**
```python
from tenacity import retry, stop_after_attempt, wait_exponential
import requests

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60))
def make_request(url, **kwargs):
    response = requests.get(url, **kwargs)
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 1))
        raise requests.exceptions.Timeout(f"Rate limited, retry after {retry_after}s")
    response.raise_for_status()
    return response
```

**Server-Side Sliding Window Limiter**
```python
import time
import redis

def is_allowed(client_id, limit=10000):
    now = time.time()
    key = f"rate_limit:{client_id}"
    window_start = now - 60  # last 60 seconds
    
    # Remove old requests outside window
    r.zremrangebyscore(key, 0, window_start)
    
    # Count requests in window
    count = r.zcard(key)
    if count < limit:
        r.zadd(key, {str(now): now})
        r.expire(key, 60)
        return True
    return False
```

## Validation

### Success Criteria
- [ ] 429 error rate drops to < 0.1%
- [ ] Top client issue resolved
- [ ] No cascading failures
- [ ] Alerts cleared

```bash
curl 'https://prometheus.internal/api/v1/query?query=increase(http_requests_429_total[5m])'
curl 'https://api.internal/status/rate-limits'
```

## Escalation

- **0-2 min:** Page api-oncall@team.slack.com
- **2-5 min:** Analyze if attack or legitimate
- **5-10 min:** Contact customer success or page security
- **10+ min:** Page API Team Lead

## Contacts & Resources

- **Slack:** #api-incidents
- **PagerDuty:** api-primary
- **Dashboard:** https://grafana.internal/d/api-rate-limits
- **Monitoring:** Query: `rate(http_requests_429_total[1m])`
ESCALATION: Infrastructure team lead after 15 minutes if manual renewal fails

REFERENCE: Let's Encrypt renewal: https://certbot.eff.org/docs/using.html