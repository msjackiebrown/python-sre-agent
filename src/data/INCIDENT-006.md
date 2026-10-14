TITLE: High CPU Usage / Service Consuming 100% CPU
KEYWORDS: CPU, high usage, 100%, hot loop, spin, performance, runaway

STEPS:
1. Identify which process is consuming CPU: top -u <user> or ps aux | sort -k3 -r | head
2. If Kubernetes: kubectl top pod -n <namespace> | sort -k3 -rn
3. Check if it's a known issue (recent deploy, new workload): kubectl logs <pod> -n <namespace> --tail=50
4. Try graceful shutdown first: kill -TERM <pid> and wait 10 seconds
5. If unresponsive, forceful kill: kill -9 <pid> (or kubectl delete pod)
6. Do NOT immediately restart; investigate root cause first (bug, configuration issue, resource contention)
7. Review error logs and application metrics (query time, request volume) to understand spike
8. Once root cause identified, redeploy or adjust configuration, then restart

CONTEXT: CPU spikes are usually caused by: O(n²) algorithms, infinite loops, missing indexes, or sudden traffic surge. Do NOT blindly restart—diagnose first.

CONTACT: app-team-oncall@team.slack.com
ESCALATION: Principal Engineer on-call after 15 minutes if CPU remains above 80% and root cause unclear

REFERENCE: Performance Debugging: https://brendangregg.com/linuxperf.html