#!/usr/bin/env python3
import os
import random
import string
import time
from io import BytesIO

import requests

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000/api/webhook/anpr")
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", "change-me")
INTERVAL_SECONDS = int(os.getenv("SIM_INTERVAL_SECONDS", "10"))
# Set SIM_DAHUA_MODE=1 to mimic Dahua ITC413 field names (plateNumber, plateImage)
DAHUA_MODE = os.getenv("SIM_DAHUA_MODE", "0") == "1"


def random_plate() -> str:
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=4))
    suffix = ''.join(random.choices(string.ascii_uppercase, k=2))
    return f"{letters}{numbers}{suffix}"


def fake_image_bytes() -> bytes:
    # Minimal binary payload for webhook upload simulation.
    return BytesIO(os.urandom(1024)).getvalue()


def main() -> None:
    mode_label = "Dahua ITC413 mode" if DAHUA_MODE else "legacy mode"
    print(f"Simulator started ({mode_label}). Sending webhook to {WEBHOOK_URL} every {INTERVAL_SECONDS}s")
    while True:
        plate = random_plate()
        if DAHUA_MODE:
            files = {"plateImage": (f"{plate}.jpg", fake_image_bytes(), "image/jpeg")}
            data = {"plateNumber": plate}
        else:
            files = {"image": (f"{plate}.jpg", fake_image_bytes(), "image/jpeg")}
            data = {"plate_number": plate}
        headers = {"X-Webhook-Token": WEBHOOK_TOKEN}

        try:
            response = requests.post(WEBHOOK_URL, data=data, files=files, headers=headers, timeout=5)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {plate} -> {response.status_code} {response.text}")
        except requests.RequestException as exc:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] request failed: {exc}")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
