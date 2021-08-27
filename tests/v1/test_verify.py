import json
from http import HTTPStatus
from datetime import datetime

from fastapi.testclient import TestClient
from slack_sdk.signature import SignatureVerifier

from app import app
from app.dependencies import verify_signature
from app.settings import settings


def test_not_verified():
    app.dependency_overrides[verify_signature] = verify_signature
    client = TestClient(app)
    res = client.post('/v1/events/', json={'type': 'url_verification', 'token': 'token'})
    assert res.status_code == HTTPStatus.FORBIDDEN


def test_verified():
    app.dependency_overrides[verify_signature] = verify_signature
    client = TestClient(app)
    timestamp = int(datetime.now().timestamp())
    data = {'type': 'url_verification', 'token': 'token'}
    verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
    signature = verifier.generate_signature(timestamp=timestamp, body=json.dumps(data))
    headers = {'x-slack-request-timestamp': str(timestamp), 'x-slack-signature': signature}
    res = client.post('/v1/events/', json=data, headers=headers)
    assert res.status_code == HTTPStatus.OK
