from __future__ import annotations

import pytest

from main import _validate_runtime_secrets, settings


def get_auth_headers(client):
    response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin'})
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_security_validation_blocks_weak_secrets_in_production(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setattr(settings, 'secret_key', 'change-me')
    monkeypatch.setattr(settings, 'admin_password', 'change-me')
    monkeypatch.setattr(settings, 'webhook_shared_secret', 'change-me')

    with pytest.raises(RuntimeError):
        _validate_runtime_secrets()


def test_system_status_requires_auth(client):
    response = client.get('/api/system/status')
    assert response.status_code == 401


def test_stats_requires_auth(client):
    response = client.get('/api/stats')
    assert response.status_code == 401


def test_logs_requires_auth(client):
    response = client.get('/api/logs')
    assert response.status_code == 401


def test_system_status_with_auth(client):
    headers = get_auth_headers(client)
    response = client.get('/api/system/status', headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert 'online' in payload
    assert 'checked_at' in payload


def test_webhook_rejects_unsupported_content_type(client, monkeypatch):
    monkeypatch.setenv('WEBHOOK_AUTH_MODE', 'token')

    response = client.post(
        '/api/webhook/anpr',
        data={'plate_number': 'AA1234BB'},
        files={'image': ('sample.gif', b'gif89a', 'image/gif')},
        headers={'X-Webhook-Token': 'webhook-secret'},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Unsupported image content type'


def test_webhook_rejects_empty_image_payload(client, monkeypatch):
    monkeypatch.setenv('WEBHOOK_AUTH_MODE', 'token')

    response = client.post(
        '/api/webhook/anpr',
        data={'plate_number': 'AA1234BB'},
        files={'image': ('sample.jpg', b'', 'image/jpeg')},
        headers={'X-Webhook-Token': 'webhook-secret'},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Empty image payload'


def test_webhook_rejects_too_large_image_payload(client, monkeypatch):
    monkeypatch.setenv('WEBHOOK_AUTH_MODE', 'token')
    monkeypatch.setenv('WEBHOOK_MAX_IMAGE_BYTES', '4')

    response = client.post(
        '/api/webhook/anpr',
        data={'plate_number': 'AA1234BB'},
        files={'image': ('sample.jpg', b'12345', 'image/jpeg')},
        headers={'X-Webhook-Token': 'webhook-secret'},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Image payload is too large'


def test_cors_allows_localhost_ports(client):
    response = client.options(
        '/api/auth/login',
        headers={
            'Origin': 'http://localhost:3999',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type,authorization',
        },
    )

    assert response.status_code == 200
    assert response.headers.get('access-control-allow-origin') == 'http://localhost:3999'
