TITLE: Database Connection Timeout During Peak Load
KEYWORDS: timeout, database, connection, pool, peak load, latency
TRIGGER: User mentions timeout + database + slow queries

STEPS:
1. Check database connection pool status
2. Increase max_connections if < 80% utilization
3. Review slow query log for long-running queries
4. If still blocking, restart database replication slave

CONTACT: db-oncall@team.slack.com
ESCALATION: Platform team lead after 15 minutes