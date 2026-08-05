---
name: Migration Guide
description: Write a step-by-step guide for migrating from one system version to another
---

# Migration Guide: API Gateway v2 to v3

## Overview

This guide covers migrating from API Gateway v2 to v3. Version 3 introduces breaking changes to authentication, rate limiting, and response formats. Plan for 2-4 hours of migration time per service.

## Prerequisites

Before starting migration:

1. Backup current configuration: Export v2 gateway config to gateway-v2-backup.yaml
2. Review breaking changes: Read the v3 changelog
3. Update client libraries: Ensure all client applications use gateway-client >= 3.0.0
4. Schedule maintenance window: Plan 30-minute downtime for cutover
5. Prepare rollback plan: Test rollback procedure in staging environment

## Breaking Changes

### Authentication

**v2**: API keys passed in X-API-Key header

**v3**: API keys passed in Authorization Bearer header

**Migration**: Update all client applications to use new header format. The v3 gateway rejects requests with X-API-Key header.

### Rate Limiting

**v2**: Rate limits applied per API key (1000 requests/hour)

**v3**: Rate limits applied per endpoint (varies by endpoint)

**Migration**: Review new rate limits for each endpoint. Update client applications to handle 429 responses with exponential backoff.

### Response Format

**v2**: Errors returned as plain text

**v3**: Errors returned as JSON with code, message, and retry_after fields

**Migration**: Update error handling in client applications to parse JSON error responses.

## Step-by-Step Migration

### Step 1: Install v3 Gateway

Download v3 gateway binary from releases page. Extract and install to /usr/local/bin/gateway-v3. Verify installation by running gateway-v3 --version.

### Step 2: Convert Configuration

Use gateway-v3 config migrate command to convert v2 config to v3 format. Review converted config and validate syntax. Common conversion issues: rate_limit field renamed to rate_limiting, auth.api_key_header removed, response.error_format removed.

### Step 3: Update Routing Rules

Edit gateway-v3.yaml and update routing rules. Note: v3 uses requests_per_second instead of v2 requests_per_hour. Divide v2 values by 3600.

### Step 4: Test in Staging

Start v3 gateway in staging environment. Run integration tests. Check logs for errors. Expected: All tests pass, no errors in logs.

### Step 5: Deploy to Production

Stop v2 gateway. Backup v2 binary for rollback. Install v3 as default gateway. Start v3 gateway. Verify health endpoint returns healthy status.

### Step 6: Monitor Post-Migration

Monitor for 1 hour after migration. Check error rate (expected < 0.1%). Check p99 latency (expected < 200ms). Check rate limit violations (expected minimal).

## Rollback Procedure

If issues arise, rollback to v2: Stop v3 gateway. Restore v2 binary. Restore v2 config. Start v2 gateway. Verify rollback by checking health endpoint.

## Troubleshooting

### Problem: 401 Unauthorized errors after migration

**Cause**: Clients still using X-API-Key header

**Solution**: Update client applications to use Authorization Bearer header

### Problem: 429 Too Many Requests errors

**Cause**: New rate limits are stricter than v2

**Solution**: Review rate limits in gateway-v3.yaml, adjust if needed, or update clients to implement backoff

### Problem: Clients cannot parse error responses

**Cause**: Clients expect plain text errors, v3 returns JSON

**Solution**: Update client error handling to parse JSON responses

## Support

- Documentation: https://docs.example.com/gateway/v3
- Migration forum: https://forum.example.com/c/gateway-migration
- Emergency support: gateway-support@example.com