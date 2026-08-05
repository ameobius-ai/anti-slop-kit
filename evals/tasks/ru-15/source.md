# Политика контроля доступа к API
## Правило 1: Принципал=ANY_ANONYMOUS, Ресурс=/api/v1/public/*, Условие=rate_limit(100/minute), Действие=ALLOW
## Правило 2: Принципал=GROUP:authenticated_users, Ресурс=/api/v1/user/*, Условие=token_valid() AND token_scope("read:user"), Действие=ALLOW
## Правило 3: Принципал=GROUP:administrators, Ресурс=/api/v1/admin/*, Условие=mfa_verified() AND ip_whitelist("10.0.0.0/8"), Действие=ALLOW
## Правило 4: Принципал=SERVICE:payment-gateway, Ресурс=/api/v1/internal/payments, Условие=mtls_certificate("payment-gateway.cert"), Действие=ALLOW
## Правило 5: Принципал=*, Ресурс=*, Действие=DENY
