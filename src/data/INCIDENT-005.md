---
id: INCIDENT-005
title: Disk Space Critical (>95% Utilized)
severity: high
keywords: "disk space filesystem full df -h inode volume storage capacity exhausted write failed"
contact: infrastructure-oncall@team.slack.com
escalate: Page Infrastructure Lead after 5min; Page Storage Team after 15min if expansion needed
---

## Description

Filesystem nearly full (> 95% capacity) causing write failures, database corruption, and service crashes. Common causes: unbounded logs, database WAL accumulation, temp file cleanup failure, unmanaged backups.

**Impact:**
- Application write failures (logs, temp files can't be written)
- Database may not start (can't write WAL)
- No new log entries (debugging impossible)
- Cascading service failures

## Detection

### Alert Triggers
- Alert: `DiskSpaceAlertCritical` (usage > 95%)
- Alert: `DiskSpaceAlertWarning` (usage > 85%)
- Manual: `df -h` shows mount at 97%

### Manual Verification
```bash
# Check all filesystems
df -h

# Check inode usage
df -i

# Find largest directories
du -sh /* | sort -rh
```

## Investigation

### Step 1: Identify Space Hog (1-2 min)
```bash
# Most common: logs
du -sh /var/log/* | sort -rh

# Database WAL
du -sh /var/lib/mysql/* | sort -rh

# Temp files
du -sh /tmp/* | sort -rh

# Docker storage
du -sh /var/lib/docker/
```

### Step 2: Check Log Rotation (30 seconds)
```bash
# Is rotation configured?
ls -la /etc/logrotate.d/

# Check if rotation happening
ls -la /var/log/application/
# Should show: app.log, app.log.1, app.log.2.gz
```

### Step 3: Assess Impact (1 min)
```bash
# Can database write?
mysql -e "SHOW GLOBAL STATUS LIKE 'Innodb_os_log_written';" 2>&1

# Application write errors?
tail -50 /var/log/syslog | grep -i 'disk\|space\|enospc'
```

## Remediation

### Phase 1: EMERGENCY (0-2 min) - FREE SPACE

**Delete Old Logs Aggressively**
```bash
# Delete logs older than 2 days
find /var/log -name "*.log" -mtime +2 -delete
find /var/log -name "*.log.1" -mtime +1 -delete

# Verify
df -h
```

**Compress Logs**
```bash
# Gzip old logs (massive savings!)
find /var/log -name "*.log.[0-9]" -type f ! -name "*.gz" -exec gzip {} \;
find /var/log -name "*.log.[0-9][0-9]" -type f ! -name "*.gz" -exec gzip {} \;

# Check compression
ls -lh /var/log/application/
# 100MB log.5 → 5MB log.5.gz
```

**Clear Temp/Cache**
```bash
# Docker cache
docker system prune -a --volumes

# Temp files
rm -rf /tmp/* /var/tmp/*

# Nginx cache
rm -rf /var/cache/nginx/*
systemctl restart nginx
```

**Verify After Cleanup**
```bash
df -h  # Should show > 10GB available
systemctl status mysql nginx application-server
tail -20 /var/log/mysql/error.log
```

### Phase 2: PREVENT RECURRENCE (2-5 min)

**Fix Log Rotation**
```bash
# Check current config
cat /etc/logrotate.d/application

# Create if missing
cat > /etc/logrotate.d/application << 'EOF'
/var/log/application/*.log {
    daily
    rotate 7              # keep 7 days
    compress              # gzip old logs
    delaycompress         # don't compress yesterday yet
    missingok             # don't error if missing
    notifempty            # don't rotate empty
    create 0640 app app   # new log permissions
}
EOF

# Test and apply
logrotate -d /etc/logrotate.d/application
logrotate -f /etc/logrotate.d/application

# Verify
ls -la /var/log/application/ | head
```

**Reduce Log Verbosity**
```yaml
# application.yml
logging:
  level:
    root: INFO          # was DEBUG
    com.company: INFO   # was TRACE
    org.springframework: WARN
```

```bash
kubectl -n production rollout restart deployment/application
watch -n 5 'du -sh /var/log/application/'
```

**Setup Volume Expansion**
```bash
# AWS example
aws ec2 modify-volume --volume-id vol-12345 --size 200

# Extend filesystem
growpart /dev/sda 1
resize2fs /dev/sda1

# Verify
df -h  # Should show 200G
```

### Phase 3: MONITOR & AUTOMATE

**Prometheus Alert Rules**
```yaml
groups:
- name: disk_alerts
  rules:
  - alert: DiskSpaceAlertCritical
    expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) > 0.95
    for: 2m
  - alert: DiskSpaceAlertWarning
    expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) > 0.85
    for: 5m
```

**Automatic Cleanup Cron**
```bash
# /etc/cron.daily/cleanup-old-logs
#!/bin/bash
find /var/log -name "*.log.*" -mtime +30 -delete
find /var/cache -type f -atime +30 -delete
df -h >> /var/log/disk-usage.log

chmod +x /etc/cron.daily/cleanup-old-logs
```

## Validation

### Success Criteria
- [ ] Disk usage < 85%
- [ ] `df -h` shows > 10GB available
- [ ] No application/database errors
- [ ] Services running normally
- [ ] Log rotation working

```bash
echo "=== Disk Status ===" && df -h && echo "" && \
echo "=== Largest Dirs ===" && du -sh /* | sort -rh | head -5 && echo "" && \
echo "=== Log Rotation ===" && ls -la /var/log/application/ | head -5 && echo "" && \
echo "=== Service Status ===" && systemctl status mysql nginx
```

## Escalation

- **0-2 min:** Page infrastructure-oncall@team.slack.com
- **2-5 min:** Execute emergency cleanup
- **5-10 min:** If still high, page Infrastructure Lead
- **10-15 min:** If expansion needed, page Storage Team

## Contacts & Resources

- **Slack:** #infrastructure-incidents
- **PagerDuty:** infra-primary
- **Monitoring:** https://grafana.internal/d/disk-usage
- **Wiki:** https://wiki.internal/runbooks/disk-cleanup

CONTACT: infrastructure-oncall@team.slack.com
ESCALATION: Storage/Infrastructure Manager after 20 minutes if manual cleanup doesn't free sufficient space

REFERENCE: Linux Disk Management: https://www.digitalocean.com/community/tutorials/how-to-manage-disk-quotas-on-linux