TITLE: Disk Space Critical / Filesystem Full
KEYWORDS: disk, full, storage, filesystem, inode, quota, critical

STEPS:
1. Check disk usage: df -h (for block usage) and df -i (for inode usage)
2. Identify mount point that is >90% full
3. Check what's consuming space: du -sh /* | sort -hr | head -20
4. Look for log files that can be archived/deleted: find /var/log -name "*.log" -mtime +30 -delete
5. Check temporary files: rm -rf /tmp/* (if safe for your service)
6. If still critical, pause logging temporarily (if acceptable) or enable log rotation if not already active
7. Restart services if they failed due to write errors: systemctl restart <service>
8. Monitor free space over next hour to ensure stabilization

CONTEXT: Filesystem full can cause cascading failures (services can't write logs, databases can't write data). Check for unmanaged temporary files and broken log rotation first.

CONTACT: infrastructure-oncall@team.slack.com
ESCALATION: Storage/Infrastructure Manager after 20 minutes if manual cleanup doesn't free sufficient space

REFERENCE: Linux Disk Management: https://www.digitalocean.com/community/tutorials/how-to-manage-disk-quotas-on-linux