TITLE: Certificate Expiration Warning / SSL/TLS Handshake Failure
KEYWORDS: certificate, SSL, TLS, handshake, expired, cert-manager, HTTPS

STEPS:
1. Check certificate expiration: openssl s_client -connect <domain:443> | grep -A 2 "Not After"
2. Or via kubectl: kubectl get certificate -n <namespace>
3. If expired or expiring within 7 days, manually trigger renewal
4. For cert-manager: kubectl annotate certificate <cert-name> -n <namespace> cert-manager.io/issue-transition-time="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" --overwrite
5. Verify renewal completed: kubectl describe certificate <cert-name> -n <namespace>
6. Restart affected services/ingress if cert was updated
7. Monitor client requests for TLS errors; confirm HTTPS traffic is normal

CONTEXT: Certificate issues cause cascading failures in HTTPS-only infrastructure. Always check cert renewal automation is enabled.

CONTACT: platform-oncall@team.slack.com
ESCALATION: Infrastructure team lead after 15 minutes if manual renewal fails

REFERENCE: Let's Encrypt renewal: https://certbot.eff.org/docs/using.html