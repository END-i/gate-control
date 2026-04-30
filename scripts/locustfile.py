"""Locust load-test scenarios for the ANPR Gate Control API.

Run against a live stack:
    locust -f scripts/locustfile.py --host http://localhost:8000 \
           --users 20 --spawn-rate 5 --run-time 60s --headless

Or open the web UI:
    locust -f scripts/locustfile.py --host http://localhost:8000

Scenarios
---------
AnprApiUser
    Simulates a typical operator session:
      - log in once, then repeatedly call stats, logs, vehicles.

WebhookUser
    Simulates ANPR cameras sending plate events at high frequency.
"""
from __future__ import annotations

import io
import random
import string

from locust import HttpUser, between, task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PLATES = [
    "AA1234BB",
    "BC5678CD",
    "EE9012FF",
    "GH3456IJ",
    "KL7890MN",
]

_WEBHOOK_TOKEN = "change-me-webhook-secret"  # must match WEBHOOK_SHARED_SECRET in .env


def _random_plate() -> str:
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    digits = "".join(random.choices(string.digits, k=4))
    suffix = "".join(random.choices(string.ascii_uppercase, k=2))
    return f"{letters}{digits}{suffix}"


def _tiny_jpeg() -> bytes:
    """Return a minimal valid 1×1 JPEG (44 bytes)."""
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
        b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
        b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e"
        b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00"
        b"\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00"
        b"\x08\x01\x01\x00\x00?\x00\xfb\xd0\xff\xd9"
    )


# ---------------------------------------------------------------------------
# Dashboard / operator scenario
# ---------------------------------------------------------------------------

class AnprApiUser(HttpUser):
    """Simulates a logged-in operator browsing the dashboard."""

    wait_time = between(0.5, 2.0)
    _token: str = ""

    def on_start(self) -> None:
        resp = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        if resp.status_code == 200:
            self._token = resp.json().get("access_token", "")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    @task(3)
    def get_stats(self) -> None:
        self.client.get("/api/stats", headers=self._headers(), name="/api/stats")

    @task(3)
    def get_logs(self) -> None:
        self.client.get(
            "/api/logs?limit=50&offset=0",
            headers=self._headers(),
            name="/api/logs",
        )

    @task(1)
    def get_vehicles(self) -> None:
        self.client.get(
            "/api/vehicles?limit=50&offset=0",
            headers=self._headers(),
            name="/api/vehicles",
        )

    @task(1)
    def health_check(self) -> None:
        self.client.get("/health", name="/health")


# ---------------------------------------------------------------------------
# Camera / webhook scenario
# ---------------------------------------------------------------------------

class WebhookUser(HttpUser):
    """Simulates ANPR cameras sending plate-read events."""

    wait_time = between(0.1, 1.0)

    @task
    def send_webhook(self) -> None:
        plate = random.choice(_PLATES)
        jpeg = _tiny_jpeg()
        self.client.post(
            "/api/webhook/anpr",
            headers={"X-Webhook-Token": _WEBHOOK_TOKEN},
            data={"plate_number": plate},
            files={"image": ("plate.jpg", io.BytesIO(jpeg), "image/jpeg")},
            name="/api/webhook/anpr",
        )
