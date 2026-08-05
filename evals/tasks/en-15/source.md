# API Access Control Policy
## Rule 1: Principal=ANY_ANONYMOUS, Resource=/api/v1/public/*, Condition=rate_limit(100/minute), Action=ALLOW
## Rule 2: Principal=GROUP:authenticated_users, Resource=/api/v1/user/*, Condition=token_valid() AND token_scope("read:user"), Action=ALLOW
## Rule 3: Principal=GROUP:administrators, Resource=/api/v1/admin/*, Condition=mfa_verified() AND ip_whitelist("10.0.0.0/8"), Action=ALLOW
## Rule 4: Principal=SERVICE:payment-gateway, Resource=/api/v1/internal/payments, Condition=mtls_certificate("payment-gateway.cert"), Action=ALLOW
## Rule 5: Principal=*, Resource=*, Action=DENY
