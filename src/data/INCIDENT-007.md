TITLE: Network Connectivity Issue / Packet Loss / DNS Failure
KEYWORDS: network, connectivity, packet loss, latency, DNS, DNS resolution

STEPS:
1. Test basic connectivity: ping -c 5 8.8.8.8 (public DNS) and note packet loss %
2. Check network interface status: ip link show or ifconfig
3. If interface is DOWN, bring it up: ip link set <interface> up
4. Test DNS resolution: nslookup google.com or dig google.com
5. If DNS fails, check /etc/resolv.conf and verify nameserver entries
6. Check routing table: route -n (or ip route show)
7. For Kubernetes pods: kubectl exec -it <pod> -n <namespace> -- /bin/sh and repeat tests
8. If pod can't reach cluster DNS (kube-dns), check coredns pod status: kubectl get pods -n kube-system | grep coredns
9. Restart coredns if not running: kubectl rollout restart deployment/coredns -n kube-system
10. Verify external connectivity via netcat: nc -zv <external-host> <port>

CONTEXT: Network issues often masquerade as application errors. Always test at the network layer first (ICMP, DNS, TCP) before assuming application bug.

CONTACT: network-team-oncall@team.slack.com
ESCALATION: Network Engineering Manager after 10 minutes if connectivity does not restore

REFERENCE: Linux Network Troubleshooting: https://www.ibm.com/cloud/learn/troubleshooting-networking-issues