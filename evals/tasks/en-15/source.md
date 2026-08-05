# API Access Control Policy

## Rule 1: Public endpoints
- Principal: ANY_ANONYMOUS
- Resource: /api/v1/public/*
- Condition: rate_limit(100/minute)
- Action: ALLOW

## Rule 2: Authenticated users
- Principal: GROUP:authenticated_users
- Resource: /api/v1/user/*
- Condition: token_valid() AND token_scope("read:user")
- Action: ALLOW

## Rule 3: Admin operations
- Principal: GROUP:administrators
- Resource: /api/v1/admin/*
- Condition: mfa_verified() AND ip_whitelist("10.0.0.0/8")
- Action: ALLOW

## Rule 4: Service-to-service
- Principal: SERVICE:payment-gateway
- Resource: /api/v1/internal/payments
- Condition: mtls_certificate("payment-gateway.cert")
- Action: ALLOW

## Rule 5: Default deny
- Principal: *
- Resource: *
- Condition: none
- Action: DENY