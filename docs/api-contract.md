# API Contract

## Scope
This document defines canonical API contracts for the ANPR Gate Control system.

## Global Rules

1. Base path: /api
2. Content type for JSON endpoints: application/json
3. Timestamps: ISO-8601 UTC with Z suffix
4. Authentication: Bearer JWT unless endpoint is explicitly public
5. Error shape:

```json
{"detail":"human-readable message"}
```

## Pagination

Use query parameters:

- limit: integer, default 50, max 200
- offset: integer, default 0

List responses must use this envelope:

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

## Date Filters

- date_from: inclusive UTC datetime
- date_to: inclusive UTC datetime
- If omitted, backend applies no bound for that side.

## Auth Endpoints

### POST /api/auth/login

Request:

```json
{
  "username": "admin",
  "password": "secret"
}
```

Success 200:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

Errors:

- 401: invalid credentials

## Vehicle Endpoints

### GET /api/vehicles

Auth required: yes
Query: limit, offset

Success 200:

```json
{
  "items": [
    {
      "id": 1,
      "license_plate": "AB1234CD",
      "status": "allowed",
      "owner_info": "string"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### POST /api/vehicles

Auth required: yes

Request:

```json
{
  "license_plate": "AB1234CD",
  "status": "blocked",
  "owner_info": "John Doe"
}
```

Success 201:

```json
{
  "id": 1,
  "license_plate": "AB1234CD",
  "status": "blocked",
  "owner_info": "John Doe"
}
```

Errors:

- 400: invalid payload
- 409: duplicate license plate

### PUT /api/vehicles/{id}

Auth required: yes

Request:

```json
{
  "license_plate": "AB1234CD",
  "status": "allowed",
  "owner_info": "John Doe"
}
```

Success 200: updated vehicle object

### DELETE /api/vehicles/{id}

Auth required: yes

Success 204: empty body

## Webhook Endpoint

### POST /api/webhook/anpr

Auth required: webhook token or HMAC depending on mode
Content type: multipart/form-data

Fields:

- plate_number: string
- image: binary file

Token mode headers:

- X-Webhook-Token

HMAC mode headers:

- X-Webhook-Timestamp
- X-Webhook-Signature

Success 200:

```json
{
  "status": "opened",
  "plate": "AB1234CD"
}
```

or

```json
{
  "status": "denied",
  "plate": "AB1234CD"
}
```

Errors:

- 401: auth failed
- 400: malformed multipart payload

## Logs Endpoints

### GET /api/logs

Auth required: yes
Query: limit, offset, plate, date_from, date_to

Success 200:

```json
{
  "items": [
    {
      "id": 1,
      "license_plate": "AB1234CD",
      "timestamp": "2026-04-29T10:00:00Z",
      "access_granted": true,
      "image_path": "media/2026/04/29/sample.jpg"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### GET /api/logs/stream

Auth required: yes
Transport: text/event-stream

Event payload data shape:

```json
{
  "id": 1,
  "license_plate": "AB1234CD",
  "timestamp": "2026-04-29T10:00:00Z",
  "access_granted": true,
  "image_path": "media/2026/04/29/sample.jpg"
}
```

Heartbeat event name: heartbeat

## Stats Endpoint

### GET /api/stats

Auth required: yes

Success 200:

```json
{
  "total_vehicles": 0,
  "today_access_total": 0,
  "today_denied_total": 0
}
```

## Manual Relay Endpoint

### POST /api/relay/trigger

Auth required: yes

Success 200:

```json
{
  "status": "ok",
  "message": "relay triggered"
}
```

Failure 502:

```json
{
  "detail": "relay trigger failed"
}
```
