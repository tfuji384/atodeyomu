from app.models import TeamConf
from http import HTTPStatus
from unittest import mock

from fastapi.testclient import TestClient

from app import app
from tests.factories import get_object

client = TestClient(app)


def test_challenge():
    challenge = 'challenge'
    res = client.post('/v1/events/', json={'type': 'url_verification', 'token': 'token', 'challenge': challenge})
    assert res.status_code == HTTPStatus.OK
    assert res.json()['challenge'] == challenge


@mock.patch('app.models.TeamConf.get', mock.Mock(side_effect=TeamConf.DoesNotExist))
def test_team_conf_does_not_exist():
    data = {
        'type': 'event_callback',
        'token': 'token',
        'team_id': 'invalid_team_id',
        'event': {
            'type': 'reaction_added',
            'user': 'U00XXXXXXX',
            'item': {
                'type': 'message',
                'channel': 'XXXXXXXXXXX',
                'ts': '1629891004.013500'
            },
            'reaction': 'atodeyomu',
            'event_ts': '1629935430.003400'
        },
    }
    res = client.post('/v1/events/', json=data)
    assert res.status_code == HTTPStatus.BAD_REQUEST


@mock.patch('app.models.TeamConf.get', get_object)
def test_reaction_not_in_team_conf():
    data = {
        'type': 'event_callback',
        'token': 'token',
        'team_id': 'invalid_team_id',
        'event': {
            'type': 'reaction_added',
            'user': 'U00XXXXXXX',
            'item': {
                'type': 'message',
                'channel': 'XXXXXXXXXXX',
                'ts': '1629891004.013500'
            },
            'reaction': 'hogehoge',
            'event_ts': '1629935430.003400'
        },
    }
    res = client.post('/v1/events/', json=data)
    assert res.status_code == HTTPStatus.OK


@mock.patch('app.models.TeamConf.get', get_object)
@mock.patch('slack_sdk.web.base_client.BaseClient.api_call', lambda x, *args, **kwargs:...)
@mock.patch('slack_sdk.web.client.WebClient.chat_getPermalink',
            lambda x, *args, **kwargs: {'permalink': 'https://example.com'})
def test_reaction_in_team_conf():
    data = {
        'type': 'event_callback',
        'token': 'token',
        'team_id': 'invalid_team_id',
        'event': {
            'type': 'reaction_added',
            'user': 'U00XXXXXXX',
            'item': {
                'type': 'message',
                'channel': 'XXXXXXXXXXX',
                'ts': '1629891004.013500'
            },
            'reaction': 'atodeyomu',
            'event_ts': '1629935430.003400'
        },
    }
    res = client.post('/v1/events/', json=data)
    assert res.status_code == HTTPStatus.OK
