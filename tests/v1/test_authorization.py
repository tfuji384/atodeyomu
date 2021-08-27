from app.models import TeamConf
from http import HTTPStatus
from typing import Any
from unittest import mock

from fastapi.testclient import TestClient
from slack_sdk.errors import SlackApiError
from moto import mock_dynamodb2

from app import app

client = TestClient(app)


class MockResponse:
    def __init__(self, data: Any = None):
        self.data = data


@mock.patch('slack_sdk.web.base_client.BaseClient.api_call', mock.Mock(side_effect=SlackApiError('', MockResponse())))
def test_authorize_invalid_code():
    response = client.get('/v1/authorize/', params={'code': 'invalid_code'})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def mock_oauth_v2_access_response(*args, **kwargs):
    data = {
        'ok': True,
        'team': {
            'id': 'T0000000000',
            'name': 'example_name'
        },
        'access_token': 'xoxb-0000000000000-0000000000000-aaaaaaaaaaaaaaaaaaaaaaaa',
        'app_id': 'example_app_id'
    }
    return MockResponse(data=data)


@mock.patch('slack_sdk.web.base_client.BaseClient.api_call', mock_oauth_v2_access_response)
@mock_dynamodb2
def test_authorize():
    TeamConf.create_table()
    response = client.get('/v1/authorize/', params={'code': 'invalid_code'})
    assert response.status_code == HTTPStatus.OK
    assert TeamConf.count() == 1


@mock.patch('slack_sdk.web.base_client.BaseClient.api_call', mock_oauth_v2_access_response)
@mock_dynamodb2
def test_re_authorize():
    TeamConf.create_table()
    TeamConf('T0000000000', access_token='access_token').save()
    response = client.get('/v1/authorize/', params={'code': 'invalid_code'})
    assert response.status_code == HTTPStatus.OK
    assert TeamConf.count() == 1
