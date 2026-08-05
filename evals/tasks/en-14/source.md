# Incident #INC-2024-447
- 2024-03-12 14:23:01 UTC: 3 consecutive 5xx errors on /api/users
- 2024-03-12 14:32:44 UTC: Error rate 847 requests/minute (baseline: 12)
- 2024-03-12 14:45:00 UTC: Root cause: connection pool exhaustion in user-db replica
- 2024-03-12 14:47:00 UTC: Mitigation: restart 4 user-db replica pods
- 2024-03-12 14:58:00 UTC: All 4 pods recovered
- 2024-03-12 15:30:00 UTC: Incident resolved
- 2024-03-12 16:00:00 UTC: Impact: 1,247 failed requests, 312 affected users
