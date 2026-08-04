# Incident report: slow queries on 28 July 2026

## Effect

Between 14:02 and 15:47 UTC, 12 percent of API requests took more than 5 seconds. No data was lost.

## Timeline (UTC)

| Time | Event |
|---|---|
| 13:58 | Release 2.3.7 goes to production. |
| 14:02 | Median query time goes from 120 ms to 4.6 s. |
| 14:09 | The on-call engineer gets the alert. |
| 14:41 | The engineer finds the cause in the cache keys. |
| 15:12 | The team starts the rollback. |
| 15:47 | Query time returns to 120 ms. |

## Cause

Release 2.3.7 added the user region to the cache key. The old keys became invalid. Each request then read from the database. The database served 40 times its usual number of reads.

## Corrections

1. Roll back release 2.3.7. Done on 28 July.
2. Add an alert on the cache hit rate below 80 percent. Done on 30 July.
3. Change the cache key in two steps: write both keys, then read the new key. Planned for 12 August.
