---
id: INCIDENT-007
title: Network Connectivity Issue / Packet Loss / DNS Failure
severity: high
keywords: "network connectivity packet loss latency DNS DNS-resolution routing kube-dns coredns network-policy"
contact: network-team-oncall@team.slack.com
escalate: Page Network Engineering Lead after 10min if connectivity not restored; Page Infrastructure VP after 30min
---

## Description

Application cannot reach external services, database, or other pods due to network layer failure. Common causes: DNS resolution failure, routing misconfiguration, network policy blocking, upstream service down, packet loss, BGP route withdrawn.

**Impact:**
- Services cannot communicate with dependencies
- Database connectivity fails → application errors
- External API calls timeout
- Cascading failures across service mesh
- Complete application unavailability if all paths blocked

## Detection

### Alert Triggers
- Alert: `DNSResolutionFailure` (failed DNS lookups > 5%)
- Alert: `PacketLossDetected` (> 1% loss)
- Alert: `ServiceConnectivityLost` (cannot reach dependency)
- Application logs: `connection refused` OR `name resolution failed` OR `timeout`

### Manual Verification
```bash
# Test basic connectivity
ping -c 5 8.8.8.8
# Look for packet loss % (0% = good, >1% = problem)

# Test DNS resolution
nslookup google.com
dig google.com
# Should return IP addresses

# Check network interface
ip link show
# All should show "UP" state

# Check routing
route -n
ip route show
```

## Investigation

### Step 1: Test Network Layers (1-2 min)

**Layer 1: Interface Up?**
```bash
# Check if interface is UP
ip link show eth0
# Should show: "BROADCAST,RUNNING,MULTICAST"
# If DOWN, bring up:
sudo ip link set eth0 up
```

**Layer 2: IP Address Assigned?**
```bash
# Check IP configuration
ip addr show
ifconfig
# Should show IPv4 address (e.g., 10.0.1.5/24)
```

**Layer 3: Can Reach Gateway?**
```bash
# Check default gateway
ip route show | grep default
# Example: default via 10.0.0.1 dev eth0

# Ping gateway
ping -c 5 10.0.0.1
# Should respond (0% packet loss)
```

**Layer 4: External Connectivity?**
```bash
# Ping public DNS
ping -c 5 8.8.8.8
# If fails: routing issue, firewall blocking, ISP issue

# Check packet loss
ping -c 100 8.8.8.8 | tail -1
# Should show 0% loss; >1% indicates network problems
```

### Step 2: Test DNS Resolution (1-2 min)

```bash
# Test DNS resolution
nslookup google.com
dig google.com
# Should return: A records with IP addresses

# Check /etc/resolv.conf
cat /etc/resolv.conf
# Should list nameservers (e.g., nameserver 8.8.8.8)

# Test specific nameserver
dig google.com @8.8.8.8  # Google DNS
dig google.com @1.1.1.1  # Cloudflare DNS

# Try different domains
nslookup prod-db-01.internal
nslookup api-prod.internal
```

### Step 3: Kubernetes-Specific Checks (1-2 min)

```bash
# Check if pods can resolve
kubectl -n production exec -it <pod-name> -- nslookup kubernetes.default
# Should resolve to cluster IP (e.g., 10.0.0.1)

# Check CoreDNS status
kubectl get pods -n kube-system | grep coredns
# Should show: coredns-* with Ready: 1/1, Status: Running

# Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50
# Look for errors

# Test DNS from pod
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup kubernetes.default
# Should work, resolving to cluster IP
```

### Step 4: Check Network Policies

```bash
# Are network policies blocking traffic?
kubectl get networkpolicy -A
kubectl get networkpolicy -n production -o yaml

# Test if specific traffic blocked
kubectl run -it --rm debug --image=busybox -- nc -zv prod-db-01 3306
# If times out: network policy likely blocking

# Inspect the policy
kubectl get networkpolicy <policy-name> -n production -o yaml
# Look for: ingress/egress allow rules
```

### Step 5: Check Service Mesh (if using Istio/Linkerd)

```bash
# Is Istio sidecar injected?
kubectl describe pod <pod-name> -n production | grep -i proxy

# Check Virtual Service config
kubectl get virtualservice -n production
kubectl describe virtualservice api-upstream -n production

# Check Destination Rules
kubectl get destinationrule -n production
```

## Remediation

### Phase 1: QUICK FIXES (0-3 min)

**If Interface Down:**
```bash
sudo ip link set eth0 up
sudo systemctl restart networking

# Verify
ip link show eth0
ping -c 5 8.8.8.8
```

**If DNS Not Working - Use Hardcoded IPs (Temporary)**
```bash
# Temporarily hardcode IP in /etc/hosts
echo "8.8.8.8 google-dns" >> /etc/hosts

# Or update application config to use IP directly
# application.yml:
# database:
#   host: 10.0.1.5  (IP instead of prod-db-01.internal)
```

**If CoreDNS Crashed:**
```bash
# Restart CoreDNS
kubectl rollout restart deployment/coredns -n kube-system
kubectl rollout status deployment/coredns -n kube-system
watch -n 2 'kubectl get pods -n kube-system | grep coredns'
# Should return to Running state
```

**If Network Policy Blocking:**
```bash
# Temporarily allow all traffic (emergency only!)
kubectl delete networkpolicy allow-only-prod -n production

# Test connectivity
kubectl run -it --rm debug --image=busybox -- nc -zv prod-db-01 3306

# If works, the policy was blocking. Don't keep it open - fix policy!
```

### Phase 2: FIX ROOT CAUSE (2-5 min)

**If DNS Issue - Check Nameservers**
```bash
# Get current nameservers
cat /etc/resolv.conf

# If missing/wrong, set correct ones
# For systemd-resolved:
sudo systemctl edit systemd-resolved
# Add:
# [Resolve]
# DNS=8.8.8.8 1.1.1.1

sudo systemctl restart systemd-resolved
```

**If Routing Issue - Check Routes**
```bash
# View routing table
ip route show
# Example output:
# default via 10.0.0.1 dev eth0
# 10.0.0.0/24 dev eth0 proto kernel scope link src 10.0.1.5

# If default route missing:
sudo ip route add default via 10.0.0.1

# Verify
ping -c 5 8.8.8.8  # should now work
```

**If Firewall Blocking (UFW/iptables)**
```bash
# Check UFW status
sudo ufw status

# Allow specific traffic
sudo ufw allow from any to any port 3306  # MySQL
sudo ufw allow from any to any port 443   # HTTPS

# Check iptables (if using iptables directly)
sudo iptables -L -n | grep -i drop

# If too restrictive, temporarily disable (emergency)
sudo iptables -F  # flush all rules
```

**If BGP Route Withdrawn (Cloud Network)**
```bash
# For AWS
# Check route propagation
aws ec2 describe-route-tables --filters Name=tag:Name,Values=prod-routes

# Check NAT gateway
aws ec2 describe-nat-gateways --filters Name=state,Values=available

# For GCP
gcloud compute routes list --filter="name:prod*"

# For Azure
az network route-table route list --resource-group prod-rg --route-table-name prod-routes
```

**If Network Policy Issue - Fix Policy**
```yaml
# BEFORE (too restrictive)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-only-prod
spec:
  podSelector: {}  # applies to all pods
  ingress: []  # no ingress allowed (blocks all!)

# AFTER (correct policy)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-prod-to-db
spec:
  podSelector:
    matchLabels:
      app: api-prod
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: production
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: production
    ports:
    - protocol: TCP
      port: 3306  # database
  - to:
    - namespaceSelector: {}  # any namespace
    ports:
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

```bash
# Apply fixed policy
kubectl apply -f network-policy.yaml
```

### Phase 3: TEST & MONITOR

```bash
# Full connectivity test
ping -c 5 8.8.8.8                    # Internet
nslookup prod-db-01.internal        # DNS
curl -v https://upstream-api.internal  # HTTPS
nc -zv prod-db-01 3306              # Database port

# From inside pod
kubectl run -it --rm debug --image=busybox -- sh
$ ping -c 5 kubernetes.default
$ nslookup kubernetes.default
$ nc -zv prod-db-01.production.svc.cluster.local 3306
```

## Validation

### Success Criteria
- [ ] `ping 8.8.8.8` returns 0% packet loss
- [ ] `nslookup <domain>` resolves successfully
- [ ] `nc -zv prod-db-01 3306` connects
- [ ] Pods can reach cluster DNS
- [ ] Application can reach all dependencies

```bash
# Comprehensive connectivity check
echo "=== Internet ===" && ping -c 3 8.8.8.8 && \
echo "=== DNS ===" && nslookup prod-db-01.internal && \
echo "=== Database ===" && nc -zv prod-db-01 3306 && \
echo "=== CoreDNS ===" && kubectl get pods -n kube-system | grep coredns && \
echo "=== Pod DNS ===" && kubectl run -it --rm debug --image=busybox -- nslookup kubernetes.default
```

## Escalation

- **0-2 min:** Page network-team-oncall@team.slack.com
- **2-5 min:** Test network layers (ICMP, DNS, TCP)
- **5-10 min:** If not resolved, page Network Engineering Lead
- **10-20 min:** Check BGP/routing with upstream ISP
- **20-30 min:** Page Infrastructure VP for escalation

## Contacts & Resources

- **Slack:** #network-incidents #infrastructure-oncall
- **PagerDuty:** network-primary, infrastructure-lead
- **Tools:**
  - `ping` - ICMP connectivity test
  - `dig` / `nslookup` - DNS resolution
  - `nc` / `telnet` - TCP port connectivity
  - `traceroute` - path to destination
  - `mtr` - combined ping + traceroute
  - `tcpdump` - packet capture
- **Kubernetes DNS:** https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/
- **Linux Networking:** https://brendangregg.com/linuxperf.html

REFERENCE: Linux Network Troubleshooting: https://www.ibm.com/cloud/learn/troubleshooting-networking-issues