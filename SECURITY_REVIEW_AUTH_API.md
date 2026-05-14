# Security Review: Auth and API Surfaces

## Scope reviewed

The repository does **not** contain exact `/src/auth` or `/src/api` directories.

For this review, the closest matching auth/API surfaces were analyzed:

- Backend API files under `/home/runner/work/gate-control/gate-control/backend/api/`
- Frontend auth/API client files:
  - `/home/runner/work/gate-control/gate-control/frontend/src/lib/api.ts`
  - `/home/runner/work/gate-control/gate-control/frontend/src/lib/stores/auth.ts`
  - `/home/runner/work/gate-control/gate-control/frontend/src/routes/login/+page.svelte`
  - `/home/runner/work/gate-control/gate-control/frontend/src/routes/logs/+page.svelte`

Supporting auth infrastructure was also checked where needed:

- `/home/runner/work/gate-control/gate-control/backend/core/security.py`
- `/home/runner/work/gate-control/gate-control/backend/core/dependencies.py`
- `/home/runner/work/gate-control/gate-control/backend/core/rate_limit.py`

## Baseline validation

The repository validation command was executed before creating this report:

- Command: `./scripts/check-all.sh`
- Result: failed immediately because `ruff` is not installed in the current environment (`/usr/bin/python3: No module named ruff`)

## Executive summary

The auth and API code already includes several good controls:

- password hashing with bcrypt/passlib
- JWT expiration handling
- role checks on privileged endpoints
- rate limiting on sensitive endpoints
- HMAC option for webhook authentication
- use of `hmac.compare_digest` for secret comparison

The highest-risk issues found are:

1. **Bearer tokens stored in `localStorage`**
2. **SSE auth token passed in the URL query string**
3. **Webhook image uploads trusted by declared MIME type only**
4. **Login protection relies mainly on IP rate limiting without stronger anti-brute-force controls**
5. **Webhook token mode permits replay if the shared token is leaked**

---

## Findings

### 1. Access token stored in `localStorage`

- **Files**
  - `/home/runner/work/gate-control/gate-control/frontend/src/lib/stores/auth.ts`
  - `/home/runner/work/gate-control/gate-control/frontend/src/lib/api.ts`
  - `/home/runner/work/gate-control/gate-control/frontend/src/routes/login/+page.svelte`
- **OWASP mapping**
  - A07: Identification and Authentication Failures
  - A03: Injection / XSS impact amplification
- **Severity**
  - High

### Why this is risky

The frontend persists the JWT access token in `localStorage`:

- `localStorage.getItem(STORAGE_KEY)` in `auth.ts`
- `localStorage.setItem(STORAGE_KEY, token)` in `auth.ts`

Any successful XSS anywhere in the frontend can extract the bearer token and replay it against the API. Because the token is added automatically to requests in `frontend/src/lib/api.ts`, theft of that token is equivalent to full session theft for its lifetime.

### Secure alternative

Prefer one of these patterns:

1. **Best default:** store the session in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie and authenticate server-side from the cookie.
2. **If a bearer token must exist in the browser:** keep the short-lived access token only in memory and store only a refresh token in an `HttpOnly` cookie.
3. Add a strong CSP and strict output-encoding, but treat that as defense-in-depth rather than the primary fix.

### Recommended implementation direction

- Move from client-managed bearer tokens to server-managed session cookies.
- If API and frontend must stay split, issue:
  - short-lived access token in memory
  - refresh token in `HttpOnly` cookie
  - rotation and revocation on refresh

---

### 2. SSE token is passed via query string

- **Files**
  - `/home/runner/work/gate-control/gate-control/backend/api/logs.py`
  - `/home/runner/work/gate-control/gate-control/frontend/src/routes/logs/+page.svelte`
  - `/home/runner/work/gate-control/gate-control/backend/core/security.py`
- **OWASP mapping**
  - A07: Identification and Authentication Failures
  - A02: Cryptographic Failures
- **Severity**
  - High

### Why this is risky

The logs stream uses:

- `GET /api/logs/stream?access_token=...`

The backend correctly limits this to a short-lived SSE-purpose token, which is better than reusing the normal access token. However, putting even short-lived secrets in URLs still creates leakage paths:

- reverse-proxy/server access logs
- browser history
- monitoring products that capture request URLs
- copy/paste or screen capture of URLs

Short lifetime reduces impact but does not remove the issue.

### Secure alternative

Safer options:

1. **Same-origin SSE with cookie auth** using an `HttpOnly` session cookie.
2. Replace `EventSource` with a `fetch`-based streaming approach where an `Authorization` header can be sent.
3. Use a **one-time opaque stream ticket** that is exchanged server-side and never used as a reusable bearer credential.

### Recommended implementation direction

- Prefer cookie-authenticated SSE if frontend and backend can share an origin.
- Otherwise, replace `EventSource` with a streaming `fetch()` reader and continue using the Authorization header.

---

### 3. Webhook image upload validation trusts client-declared content type

- **Files**
  - `/home/runner/work/gate-control/gate-control/backend/api/webhook.py`
- **OWASP mapping**
  - A05: Security Misconfiguration
  - A08: Software and Data Integrity Failures
  - A03: Injection, if uploaded content is later rendered unsafely
- **Severity**
  - High

### Why this is risky

`_save_image_async()` allows uploads based on:

- declared `image.content_type`
- file size
- file suffix normalization

It does **not** verify the actual file bytes before storing the upload. An attacker who obtains webhook access could submit a non-image payload with an allowed MIME type and extension. If that file is later served from the application origin or opened in a browser context, it can become an XSS or content-hosting problem.

### Secure alternative

Add server-side file validation before storage:

1. Validate file signature / magic bytes.
2. Decode the image with a trusted imaging library.
3. Re-encode the image into a safe output format (for example JPEG/PNG) to strip embedded active content and metadata.
4. Serve uploaded media from a separate static/media domain with restrictive headers.

### Recommended implementation direction

- Reject files that cannot be decoded as real images.
- Re-encode accepted uploads.
- Serve media with safe headers such as:
  - `Content-Type` based on validated output
  - `Content-Disposition: attachment` where practical
  - restrictive CSP on the media host

---

### 4. Login hardening is incomplete against distributed brute-force attacks

- **Files**
  - `/home/runner/work/gate-control/gate-control/backend/api/auth.py`
  - `/home/runner/work/gate-control/gate-control/backend/core/rate_limit.py`
- **OWASP mapping**
  - A07: Identification and Authentication Failures
- **Severity**
  - Medium

### Why this is risky

The login endpoint does a good job of returning a generic `"Invalid credentials"` response and enforcing IP-based rate limiting. However, IP-only throttling is weak against:

- distributed password spraying
- botnets rotating source IPs
- attacks focused on one account from many IPs

There is also no evidence here of:

- per-account throttling
- temporary lockout / exponential backoff
- MFA for sensitive users

### Secure alternative

Layer multiple defenses:

1. Per-IP rate limiting
2. Per-username or per-account rate limiting
3. Progressive delay or temporary lockout after repeated failures
4. MFA for administrative users
5. Alerting on repeated failed logins

### Recommended implementation direction

- Keep the current generic error responses.
- Add a second limiter keyed by normalized username.
- Add step-up auth or MFA for admin/operator roles.

---

### 5. Webhook token mode is replayable if the shared token leaks

- **Files**
  - `/home/runner/work/gate-control/gate-control/backend/api/webhook.py`
  - `/home/runner/work/gate-control/gate-control/backend/core/config.py`
- **OWASP mapping**
  - A07: Identification and Authentication Failures
- **Severity**
  - Medium

### Why this is risky

When `WEBHOOK_AUTH_MODE=token`, the webhook accepts a static shared secret from `X-Webhook-Token`. This authenticates the sender but does not provide freshness or replay resistance. Anyone who captures or leaks the token can replay requests until the secret is rotated.

The HMAC mode is stronger because it includes:

- a timestamp
- body binding
- a maximum skew check

### Secure alternative

Prefer authenticated request signing over a static bearer secret:

1. Make HMAC mode the only production mode.
2. Include timestamp and nonce / event ID in the signed material.
3. Reject duplicate nonces server-side.
4. Rotate webhook signing keys regularly.

### Recommended implementation direction

- Deprecate plain token mode for production.
- Require HMAC with freshness guarantees.

---

### 6. Backend error detail is surfaced directly to the UI

- **Files**
  - `/home/runner/work/gate-control/gate-control/frontend/src/lib/api.ts`
  - `/home/runner/work/gate-control/gate-control/frontend/src/routes/login/+page.svelte`
  - `/home/runner/work/gate-control/gate-control/frontend/src/routes/+page.svelte`
  - `/home/runner/work/gate-control/gate-control/frontend/src/routes/+layout.svelte`
  - `/home/runner/work/gate-control/gate-control/frontend/src/routes/logs/+page.svelte`
- **OWASP mapping**
  - A05: Security Misconfiguration
  - A09: Security Logging and Monitoring Failures
- **Severity**
  - Medium

### Why this is risky

`frontend/src/lib/api.ts` raises an error using `maybeJson?.detail ?? response.statusText`, and several pages display `error.message` directly.

Today many backend messages are generic, which helps. But this pattern means any future sensitive backend detail could be exposed directly in the UI without an additional review gate.

### Secure alternative

Use structured error handling:

1. Backend returns stable error codes.
2. Frontend maps codes to safe, localized user messages.
3. Detailed diagnostics stay server-side and are tied to a correlation/request ID.

### Recommended implementation direction

- Replace direct display of backend `detail` values with a message map.
- Reserve raw backend details for logs and admin diagnostics only.

---

### 7. JWT design is minimal and would benefit from stronger anti-confusion controls

- **Files**
  - `/home/runner/work/gate-control/gate-control/backend/core/security.py`
  - `/home/runner/work/gate-control/gate-control/backend/core/dependencies.py`
  - `/home/runner/work/gate-control/gate-control/backend/api/auth.py`
- **OWASP mapping**
  - A07: Identification and Authentication Failures
  - A02: Cryptographic Failures
- **Severity**
  - Medium

### Why this is risky

The JWT implementation includes expiration and subject, which is a solid minimum. It does not appear to include stronger contextual claims such as:

- issuer (`iss`)
- audience (`aud`)
- token ID (`jti`)
- explicit token type for standard access tokens

This increases the risk of token confusion or weak revocation options as the system grows.

### Secure alternative

Harden the token format:

1. Include `iss`, `aud`, `iat`, and `jti`
2. Validate issuer and audience on decode
3. Distinguish access, refresh, and SSE tokens explicitly
4. Add revocation/version checks for sensitive sessions

### Recommended implementation direction

- Keep the current expiration behavior.
- Add audience/issuer validation and token identifiers before expanding integration scope.

---

## Positive controls already present

The following controls are good and should be preserved:

- Generic invalid-credential response in `/backend/api/auth.py`
- Role enforcement via `require_roles(...)`
- Rate limiting on login, webhook, relay trigger, and sensitive endpoints
- `hmac.compare_digest(...)` for webhook secret comparison
- Timestamp skew enforcement in HMAC webhook mode
- Short-lived SSE-specific token instead of reusing the main access token

## Priority remediation order

1. **Move auth tokens out of `localStorage`**
2. **Stop putting stream credentials in URL query strings**
3. **Perform real image validation and re-encoding for webhook uploads**
4. **Add per-account brute-force protections and MFA for admin access**
5. **Remove or deprecate static-token webhook mode**
6. **Replace raw backend error passthrough with safe frontend message mapping**
7. **Harden JWT claim validation for future growth**

## Secure implementation patterns to prefer

### Authentication/session management

- `HttpOnly` + `Secure` + `SameSite` cookies
- short-lived access credentials
- refresh token rotation
- MFA for privileged users
- per-user and per-IP rate limits

### File handling

- magic-byte validation
- decode and re-encode uploads
- separate media host/origin
- restrictive response headers

### API error handling

- stable backend error codes
- safe frontend message mapping
- correlation IDs for debugging

### Webhook security

- HMAC-signed requests
- timestamp + nonce
- replay detection
- key rotation

## Overall conclusion

The codebase already shows good security intent, especially around generic auth failures, role checks, rate limiting, and optional HMAC verification. The main gaps are around **browser token handling**, **URL-based stream authentication**, and **upload validation**. Fixing those three areas first would produce the largest immediate security improvement against common OWASP Top 10 attack paths.
