# Postmortem: Incident #INC-2024-447

## Summary

On 2024-03-12, a connection pool exhaustion in the user-db replica caused elevated error rates on the /api/users endpoint. The incident lasted 35 minutes (14:23:01 to 14:58:00 UTC) and affected 312 users with 1,247 failed requests.

## Detection

- **2024-03-12 14:23:01 UTC:** Monitoring detected 3 consecutive 5xx errors on /api/users
- **2024-03-12 14:23:15 UTC:** PagerDuty alerted on-call engineer
- **2024-03-12 14:25:00 UTC:** On-call engineer acknowledged the alert

## Response

- **2024-03-12 14:32:44 UTC:** Error rate climbed to 847 requests/minute (baseline: 12 requests/minute)
- **2024-03-12 14:45:00 UTC:** Root cause identified: connection pool exhaustion in user-db replica

## Mitigation

- **2024-03-12 14:47:00 UTC:** Mitigation deployed: restart user-db replica pods (4 instances)
- **2024-03-12 14:52:00 UTC:** 2 pods recovered, error rate dropped to 312 requests/minute
- **2024-03-12 14:58:00 UTC:** All 4 pods recovered, error rate back to baseline (12 requests/minute)
- **2024-03-12 15:30:00 UTC:** Incident marked resolved

## Impact

- **2024-03-12 16:00:00 UTC:** Customer impact report generated
- **Failed requests:** 1,247
- **Affected users:** 312

## Follow-up Actions

- **2024-03-13 10:00:00 UTC:** Postmortem meeting scheduled
- **2024-03-13 14:00:00 UTC:** Root cause fix merged to main branch

## Lessons Learned

1. Connection pool exhaustion in user-db replica was the root cause
2. Restarting pods was effective mitigation (all 4 recovered within 11 minutes)
3. Monitoring detected the issue within 14 seconds of first error
4. Full resolution achieved in 35 minutes from detection
