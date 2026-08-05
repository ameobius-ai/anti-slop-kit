# Incident #INC-2024-447 Timeline

- 2024-03-12 14:23:01 UTC: Monitoring detects 3 consecutive 5xx errors on /api/users
- 2024-03-12 14:23:15 UTC: PagerDuty alerts on-call engineer
- 2024-03-12 14:25:00 UTC: On-call acknowledges alert
- 2024-03-12 14:32:44 UTC: Error rate climbs to 847 requests/minute (baseline: 12 requests/minute)
- 2024-03-12 14:45:00 UTC: Root cause identified: connection pool exhaustion in user-db replica
- 2024-03-12 14:47:00 UTC: Mitigation deployed: restart user-db replica pods (4 instances)
- 2024-03-12 14:52:00 UTC: 2 pods recovered, error rate drops to 312 requests/minute
- 2024-03-12 14:58:00 UTC: All 4 pods recovered, error rate back to baseline (12 requests/minute)
- 2024-03-12 15:30:00 UTC: Incident marked resolved
- 2024-03-12 16:00:00 UTC: Customer impact report generated: 1,247 failed requests, 312 affected users
- 2024-03-13 10:00:00 UTC: Postmortem meeting scheduled
- 2024-03-13 14:00:00 UTC: Root cause fix merged to main branch
