from __future__ import annotations

import api.webhook as webhook_module


def _auth_headers(client) -> dict[str, str]:
    response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin'})
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_webhook_opens_gate_for_allowed_vehicle(client, monkeypatch):
    monkeypatch.setenv('WEBHOOK_AUTH_MODE', 'token')

    headers = _auth_headers(client)
    create_vehicle = client.post(
        '/api/vehicles',
        json={'license_plate': 'AA1234BB', 'status': 'allowed'},
        headers=headers,
    )
    assert create_vehicle.status_code == 201

    called = {'count': 0}

    async def fake_trigger_relay() -> bool:
        called['count'] += 1
        return True

    monkeypatch.setattr(webhook_module, 'trigger_relay', fake_trigger_relay)

    webhook_response = client.post(
        '/api/webhook/anpr',
        data={'plate_number': 'AA1234BB'},
        files={'image': ('sample.jpg', b'data', 'image/jpeg')},
        headers={'X-Webhook-Token': 'webhook-secret', 'X-Event-Id': 'evt-allowed-1'},
    )

    assert webhook_response.status_code == 200
    payload = webhook_response.json()
    assert payload['status'] == 'opened'
    assert payload['relay_triggered'] is True
    assert called['count'] == 1


def test_webhook_denies_blocked_vehicle_and_does_not_trigger_relay(client, monkeypatch):
    monkeypatch.setenv('WEBHOOK_AUTH_MODE', 'token')

    headers = _auth_headers(client)
    create_vehicle = client.post(
        '/api/vehicles',
        json={'license_plate': 'CC5678DD', 'status': 'blocked'},
        headers=headers,
    )
    assert create_vehicle.status_code == 201

    called = {'count': 0}

    async def fake_trigger_relay() -> bool:
        called['count'] += 1
        return True

    monkeypatch.setattr(webhook_module, 'trigger_relay', fake_trigger_relay)

    webhook_response = client.post(
        '/api/webhook/anpr',
        data={'plate_number': 'CC5678DD'},
        files={'image': ('sample.jpg', b'data', 'image/jpeg')},
        headers={'X-Webhook-Token': 'webhook-secret', 'X-Event-Id': 'evt-blocked-1'},
    )

    assert webhook_response.status_code == 200
    payload = webhook_response.json()
    assert payload['status'] == 'denied'
    assert payload['relay_triggered'] is False
    assert called['count'] == 0
