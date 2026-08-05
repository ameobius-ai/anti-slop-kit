# Payment Gateway API - Client Implementation Guide

This document describes the three main API endpoints you'll use to integrate with our payment gateway.

## Creating Charges

Use `POST /v1/charges` to create a new payment.

**Important:** You can make up to 100 requests per minute. If you exceed this limit, you'll get a 429 error.

**Required headers:**
- `X-API-Key`: Your API key
- `Idempotency-Key`: A unique key to prevent duplicate charges
- `Content-Type: application/json`

**Response codes:**
- `201`: Charge created successfully
- `400`: Your request was invalid (check the parameters)
- `402`: Payment failed (e.g., insufficient funds)
- `429`: Rate limit exceeded (wait and retry)

## Retrieving Charge Details

Use `GET /v1/charges/{id}` to fetch details about an existing charge.

**Rate limit:** 500 requests per minute.

**Required headers:**
- `X-API-Key`: Your API key

**Response codes:**
- `200`: Charge found
- `404`: Charge not found (check the ID)

## Creating Refunds

Use `POST /v1/refunds` to refund a previous charge.

**Important:** You can make up to 50 requests per minute.

**Required headers:**
- `X-API-Key`: Your API key
- `Idempotency-Key`: A unique key to prevent duplicate refunds

**Response codes:**
- `201`: Refund created successfully
- `400`: Your request was invalid
