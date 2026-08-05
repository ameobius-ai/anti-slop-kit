---
name: Отчёт об инциденте
description: Написать отчёт об инциденте для производственного сбоя
---

# Incident Report: Database Connection Pool Exhaustion

## Context

Production database experienced connection pool exhaustion on 2026-08-05 at 14:30 UTC, causing 45 minutes of degraded service. This report documents the incident, root cause, and corrective actions.

## Timeline

**14:30 UTC** - Monitoring alerts fire: database connection count exceeds 95% threshold

**14:32 UTC** - On-call engineer acknowledges alert and begins investigation

**14:35 UTC** - Connection pool metrics show 195/200 connections active, 47 requests queued

**14:38 UTC** - Root cause identified: new deployment introduced connection leak in user service

**14:42 UTC** - Rollback initiated to previous stable version

**14:45 UTC** - Rollback complete, connection count drops to 85/200

**15:15 UTC** - All systems nominal, incident declared resolved

## Root Cause

The user service deployed at 14:00 UTC contained a code path that opened database connections but failed to close them in error scenarios. Specifically, the getUserProfile() function called db.query() without wrapping it in a try-finally block or using context managers.

When the function threw exceptions (which occurred in 2% of requests due to malformed user IDs), the connection remained open. Over 30 minutes, these leaked connections accumulated until the pool was exhausted.

## Impact

**Duration**: 45 minutes (14:30 - 15:15 UTC)

**Affected users**: Approximately 12,000 requests failed with 503 Service Unavailable

**Business impact**:
- 340 failed checkout attempts (estimated $68,000 in lost revenue)
- 890 failed login attempts
- 1,200 customer support tickets generated

## Corrective Actions

### Immediate (completed)

1. Rolled back to version 2.4.1 (stable)
2. Added connection pool monitoring dashboard
3. Implemented connection timeout alerts at 80% threshold

### Short-term (by 2026-08-12)

1. Audit all database connection usage in user service
2. Add integration test that verifies connection cleanup on exceptions
3. Implement connection pool health check endpoint

### Long-term (by 2026-09-30)

1. Migrate to connection pool library with automatic leak detection
2. Add static analysis rule to detect unclosed connections
3. Create runbook for connection pool exhaustion scenarios

## Lessons Learned

1. **Connection management requires defensive coding**: Always use context managers or try-finally blocks when managing resources
2. **Monitoring thresholds should be conservative**: 95% threshold was too high; 80% provides better early warning
3. **Deployment rollback capability is critical**: Fast rollback prevented longer outage
4. **Testing should include error paths**: Unit tests covered success path but not exception scenarios

## References

- Monitoring dashboard: https://grafana.internal/d/db-connections
- Deployment logs: https://kibana.internal/app/discover#/deploy-2026-08-05
- Incident channel: #incident-2026-08-05-db-pool