TITLE: Service Returns 5xx Errors
KEYWORDS: error, 500, 502, 503, service down, unavailable

STEPS:
1. Check service health endpoint: GET /health
2. Review recent logs for panic/crash messages
3. Verify dependent services (database, cache, API) are reachable
4. If unresponsive, trigger graceful restart
5. Monitor for recovery; alert on-call if not recovered in 2 min

CONTACT: platform-oncall@team.slack.com
ESCALATION: SRE manager after 5 minutes