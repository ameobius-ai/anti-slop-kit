# Payment Gateway API Contract

## Endpoint 1: POST /v1/charges
- Rate Limit: 100 requests per 60 seconds.
- Required Headers: `X-API-Key`, `Idempotency-Key`, `Content-Type: application/json`.
- Status Codes: 201 (Created), 400 (Invalid Request), 402 (Payment Failed), 429 (Rate Limited).

## Endpoint 2: GET /v1/charges/{id}
- Rate Limit: 500 requests per 60 seconds.
- Required Headers: `X-API-Key`.
- Status Codes: 200 (OK), 404 (Not Found).

## Endpoint 3: POST /v1/refunds
- Rate Limit: 50 requests per 60 seconds.
- Required Headers: `X-API-Key`, `Idempotency-Key`.
- Status Codes: 201 (Created), 400 (Invalid Request).
