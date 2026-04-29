import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from api.webhook import _verify_webhook_hmac


def _build_signature(secret: str, timestamp: str, raw_body: bytes) -> str:
    return hmac.new(secret.encode('utf-8'), timestamp.encode('utf-8') + raw_body, hashlib.sha256).hexdigest()


def test_verify_hmac_valid(monkeypatch):
    monkeypatch.setenv('WEBHOOK_HMAC_SECRET', 'hmac-secret')
    monkeypatch.setenv('WEBHOOK_MAX_SKEW_SECONDS', '300')

    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    raw_body = b'test-body'
    signature = _build_signature('hmac-secret', timestamp, raw_body)

    _verify_webhook_hmac(raw_body, timestamp, signature)


def test_verify_hmac_invalid_signature(monkeypatch):
    monkeypatch.setenv('WEBHOOK_HMAC_SECRET', 'hmac-secret')
    monkeypatch.setenv('WEBHOOK_MAX_SKEW_SECONDS', '300')

    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    with pytest.raises(HTTPException) as exc:
        _verify_webhook_hmac(b'test-body', timestamp, 'bad-signature')

    assert exc.value.status_code == 401


def test_verify_hmac_stale_timestamp(monkeypatch):
    monkeypatch.setenv('WEBHOOK_HMAC_SECRET', 'hmac-secret')
    monkeypatch.setenv('WEBHOOK_MAX_SKEW_SECONDS', '300')

    stale_time = (datetime.now(timezone.utc) - timedelta(seconds=301)).isoformat().replace('+00:00', 'Z')
    signature = _build_signature('hmac-secret', stale_time, b'test-body')

    with pytest.raises(HTTPException) as exc:
        _verify_webhook_hmac(b'test-body', stale_time, signature)

    assert exc.value.status_code == 401


def test_webhook_token_mode_works(client, monkeypatch):
    monkeypatch.setenv('WEBHOOK_AUTH_MODE', 'token')

    response = client.post(
        '/api/webhook/anpr',
        data={'plate_number': 'AA1234BB'},
        files={'image': ('sample.jpg', b'data', 'image/jpeg')},
        headers={'X-Webhook-Token': 'webhook-secret'},
    )

    assert response.status_code == 200


def test_webhook_hmac_mode_enforced(client, monkeypatch):
    monkeypatch.setenv('WEBHOOK_AUTH_MODE', 'hmac')

    response = client.post(
        '/api/webhook/anpr',
        data={'plate_number': 'AA1234BB'},
        files={'image': ('sample.jpg', b'data', 'image/jpeg')},
        headers={'X-Webhook-Token': 'webhook-secret'},
    )

    assert response.status_code == 401


def test_webhook_hmac_mode_valid_signature(client, monkeypatch):
    monkeypatch.setenv('WEBHOOK_AUTH_MODE', 'hmac')

    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    boundary = 'X-BOUNDARY-12345'
    body = (
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="plate_number"\r\n\r\n'
        'AA1234BB\r\n'
        f'--{boundary}\r\n'
        'Content-Disposition: form-data; name="image"; filename="sample.jpg"\r\n'
        'Content-Type: image/jpeg\r\n\r\n'
        'data\r\n'
        f'--{boundary}--\r\n'
    ).encode('utf-8')
    signature = _build_signature('hmac-secret', timestamp, body)

    response = client.post(
        '/api/webhook/anpr',
        data=body,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'X-Webhook-Timestamp': timestamp,
            'X-Webhook-Signature': signature,
        },
    )

    assert response.status_code == 200
