from __future__ import annotations


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


def test_webhook_denies_blocked_vehicle_and_does_not_trigger_relay(client, monkeypatch):
    monkeypatch.setenv('WEBHOOK_AUTH_MODE', 'token')

    headers = _auth_headers(client)
    create_vehicle = client.post(
        '/api/vehicles',
        json={'license_plate': 'CC5678DD', 'status': 'blocked'},
        headers=headers,
    )
    assert create_vehicle.status_code == 201

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


def test_webhook_accepts_dahua_camelcase_field_names(client, monkeypatch):
    """Dahua ITC413-PW4D-IZ1 sends plateNumber and plateImage instead of plate_number and image."""
    monkeypatch.setenv('WEBHOOK_AUTH_MODE', 'token')

    headers = _auth_headers(client)
    create_vehicle = client.post(
        '/api/vehicles',
        json={'license_plate': 'ITC413AA', 'status': 'allowed'},
        headers=headers,
    )
    assert create_vehicle.status_code == 201

    webhook_response = client.post(
        '/api/webhook/anpr',
        data={'plateNumber': 'ITC413AA'},
        files={'plateImage': ('plate.jpg', b'data', 'image/jpeg')},
        headers={'X-Webhook-Token': 'webhook-secret', 'X-Event-Id': 'evt-dahua-1'},
    )

    assert webhook_response.status_code == 200
    payload = webhook_response.json()
    assert payload['status'] == 'opened'
    assert payload['plate'] == 'ITC413AA'
