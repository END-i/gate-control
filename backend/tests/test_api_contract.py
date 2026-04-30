"""API contract tests — verify that every documented endpoint returns the
correct JSON shape and status code.

These tests run entirely in-memory (SQLite) and do not require a running
server.  They catch schema drift early: if a field is renamed or removed the
corresponding assertion will fail before the change reaches CI.

Reference: docs/api-contract.md
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client) -> str:
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

def test_health_shape(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"status"}
    assert body["status"] == "ok"


# ---------------------------------------------------------------------------
# /api/auth
# ---------------------------------------------------------------------------

def test_login_returns_token_shape(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 0
    assert body["token_type"] == "bearer"
    assert "role" in body
    assert isinstance(body["role"], str)


def test_login_wrong_password_returns_401(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401
    assert "detail" in resp.json()


def test_auth_me_shape(client):
    token = _login(client)
    resp = client.get("/api/auth/me", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"username", "role"}
    assert body["username"] == "admin"
    assert isinstance(body["role"], str)


# ---------------------------------------------------------------------------
# /api/vehicles
# ---------------------------------------------------------------------------

def test_vehicles_list_requires_auth(client):
    resp = client.get("/api/vehicles")
    assert resp.status_code == 401


def test_vehicles_list_shape(client):
    token = _login(client)
    resp = client.get("/api/vehicles", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "limit", "offset"}
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)
    assert isinstance(body["limit"], int)
    assert isinstance(body["offset"], int)


def test_vehicle_create_returns_201_and_shape(client):
    token = _login(client)
    resp = client.post(
        "/api/vehicles",
        json={"license_plate": "CONTRACT01", "status": "allowed"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert set(body.keys()) >= {"id", "license_plate", "status"}
    assert body["license_plate"] == "CONTRACT01"
    assert body["status"] == "allowed"
    assert isinstance(body["id"], int)


def test_vehicle_create_duplicate_returns_409(client):
    token = _login(client)
    payload = {"license_plate": "DUPL01", "status": "blocked"}
    client.post("/api/vehicles", json=payload, headers=_auth(token))
    resp = client.post("/api/vehicles", json=payload, headers=_auth(token))
    assert resp.status_code == 409


def test_vehicle_delete_returns_204(client):
    token = _login(client)
    create = client.post(
        "/api/vehicles",
        json={"license_plate": "DEL01", "status": "blocked"},
        headers=_auth(token),
    )
    vid = create.json()["id"]
    resp = client.delete(f"/api/vehicles/{vid}", headers=_auth(token))
    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# /api/logs
# ---------------------------------------------------------------------------

def test_logs_list_requires_auth(client):
    resp = client.get("/api/logs")
    assert resp.status_code == 401


def test_logs_list_shape(client):
    token = _login(client)
    resp = client.get("/api/logs", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"items", "total", "limit", "offset"}
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)


# ---------------------------------------------------------------------------
# /api/stats
# ---------------------------------------------------------------------------

def test_stats_shape(client):
    token = _login(client)
    resp = client.get("/api/stats", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    required = {"total_vehicles", "today_access_total", "today_denied_total"}
    assert required <= set(body.keys())
    for key in required:
        assert isinstance(body[key], int), f"{key} should be int"


# ---------------------------------------------------------------------------
# /api/system/status
# ---------------------------------------------------------------------------

def test_system_status_shape(client):
    token = _login(client)
    resp = client.get("/api/system/status", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"online", "checked_at"}
    assert isinstance(body["online"], bool)
    assert isinstance(body["checked_at"], str)
    # checked_at should be ISO-8601
    assert "T" in body["checked_at"]


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

def test_404_uses_detail_envelope(client):
    resp = client.get("/api/does-not-exist-xyz")
    assert resp.status_code == 404
    assert "detail" in resp.json()
