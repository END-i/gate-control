# Camera Setup Guide

## Karsun JS-LPRO1 (Edge Computing mode)

> **Note:** Some API endpoint paths and payload field names are marked **⚠️ pending vendor confirmation**. Update this document once the official Karsun HTTP API specification is received.

### Network configuration

| Setting | Recommended value |
|---------|------------------|
| IP address | Static, e.g. `192.168.1.100` |
| Subnet mask | `255.255.255.0` |
| Default gateway | Router IP |
| HTTP event push URL | `http://<server-ip>:8000/api/webhook/camera` |
| HTTP event auth | ⚠️ Pending — configure to match `WEBHOOK_AUTH_MODE` in server `.env` |

### HTTP event push (webhook) configuration

Configure the camera to send an HTTP POST notification on each plate recognition event.

| Field | Value |
|-------|-------|
| Protocol | HTTP POST |
| URL | `http://<server-ip>:8000/api/webhook/camera` |
| Content-Type | `multipart/form-data` |
| Auth header | `X-Webhook-Token: <WEBHOOK_SHARED_SECRET>` ⚠️ pending confirmation of supported auth mechanism |

#### Expected payload fields (⚠️ field names pending vendor documentation)

| Field name | Type | Description |
|-----------|------|-------------|
| `plate_number` | string | Recognised licence plate (server also accepts `plateNumber`) |
| `image` | binary | Plate image JPEG (server also accepts `plateImage`) |
| `direction` | string | `approach` or `leave` (optional) |
| `dateTime` | string | Camera-local ISO-8601 timestamp (optional, informational) |

### Whitelist / Blacklist API (⚠️ pending vendor documentation)

These endpoints will be called by the server to sync the vehicle list to camera memory.

| Operation | Method | Path | Notes |
|-----------|--------|------|-------|
| Add to whitelist | POST | `/api/whitelist/add` ⚠️ | Payload format TBD |
| Remove from whitelist | POST | `/api/whitelist/remove` ⚠️ | Payload format TBD |
| Trigger relay (manual open) | POST | `/api/relay` ⚠️ | Payload format TBD |

Server config variables (in `.env`):

```env
KARSUN_IP=http://192.168.1.100
KARSUN_USERNAME=admin
KARSUN_PASSWORD=your-camera-password
KARSUN_RELAY_PATH=/api/relay
KARSUN_WHITELIST_ADD_PATH=/api/whitelist/add
KARSUN_WHITELIST_REMOVE_PATH=/api/whitelist/remove
```

### Entry / exit flow

- **Entry:** Induction loop → camera scans plate → camera checks internal whitelist → camera closes relay → camera sends HTTP log to server
- **Exit:** Induction loop wired directly to barrier controller (hardware-only, no server involvement)

---

## Dahua ITC413-PW4D-IZ1 (sensor-only mode)

The Dahua camera acts as a pure sensor; all access decisions are made by the FastAPI backend.

### Network configuration

| Setting | Recommended value |
|---------|------------------|
| IP address | Static, e.g. `192.168.1.101` |
| HTTP event push protocol | ITSAPI (`multipart/form-data` POST) |
| Push URL | `http://<server-ip>:8000/api/webhook/camera` |

### Authentication

The server supports both token/HMAC and **HTTP Basic Auth** for incoming camera webhooks.

Recommended for Dahua ITSAPI:

1. Set `WEBHOOK_AUTH_MODE=basic` in backend `.env`
2. Set `WEBHOOK_BASIC_USERNAME` / `WEBHOOK_BASIC_PASSWORD`
3. Configure Dahua event push credentials to the same username/password

Alternative fallback: configure custom camera header and keep `WEBHOOK_AUTH_MODE=token` with `WEBHOOK_SHARED_SECRET`.

### ITSAPI payload fields sent by camera

| Field | Type | Notes |
|-------|------|-------|
| `plateNumber` | string | Server normalises to `plate_number` |
| `plateImage` | binary | Server accepts both `image` and `plateImage` |
| `channelName` | string | Informational |
| `dateTime` | string | Camera-local timestamp |
| `direction` | string | `approach` / `leave` |
| `country` | string | Plate country code |
| `plateColor` | string | Plate background colour |
| `vehicleColor` | string | Vehicle body colour |
| `speed` | string | km/h if speed detection enabled |

### Relay trigger

The server sends an HTTP POST to `RELAY_IP` using Basic Auth (`RELAY_USERNAME` / `RELAY_PASSWORD`) to trigger the camera's built-in Digital Output relay.

Alternative: Dahua CGI command `POST /cgi-bin/accessControl.cgi` — evaluate and document decision (see plan.md TODO).
