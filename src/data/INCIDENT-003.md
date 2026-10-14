TITLE: Memory Leak Leading to OOM (Out of Memory) Kill
KEYWORDS: memory, leak, OOM, out of memory, killed, crash, heap

STEPS:
1. SSH to affected pod/instance
2. Check memory usage: free -h or kubectl describe node <node>
3. Identify process consuming memory: top -o %MEM or kubectl top pod
4. Review application logs for memory-related warnings
5. If OOM killer invoked, restart service: systemctl restart <service>
6. After restart, monitor memory over next 30 minutes
7. If leak persists, escalate to application team for code review

CONTEXT: Memory leaks are often caused by improper resource cleanup. Do NOT kill the process unless OOM killer already did—collect diagnostics first.

CONTACT: app-team-oncall@team.slack.com
ESCALATION: Application Engineering Manager after 10 minutes if manual restart doesn't resolve

REFERENCE: Kubernetes OOM docs: https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/