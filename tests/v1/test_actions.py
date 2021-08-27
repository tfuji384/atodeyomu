import json
from http import HTTPStatus
from unittest import mock

from fastapi.testclient import TestClient
from moto import mock_dynamodb2

from app import app, models
from tests.factories import get_object

client = TestClient(app)


def test_redirect_to_view_submission():
    payload = {
        'type': 'view_submission',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/', data=data, allow_redirects=False)
    assert res.status_code == HTTPStatus.TEMPORARY_REDIRECT
    assert res.headers['location'] == './view_submission/'


def test_redirect_to_shortcuts():
    payload = {
        'type': 'shortcut',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/', data=data, allow_redirects=False)
    assert res.status_code == HTTPStatus.TEMPORARY_REDIRECT
    assert res.headers['location'] == './shortcuts/'


def test_redirect_to_message():
    payload = {
        'type': 'block_actions',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'container': {
            'type': 'message'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/', data=data, allow_redirects=False)
    assert res.status_code == HTTPStatus.TEMPORARY_REDIRECT
    assert res.headers['location'] == './message/'


@mock.patch('app.models.TeamConf.get', mock.Mock(side_effect=models.TeamConf.DoesNotExist))
def test_shortcut_teamconf_doesnot_exists():
    payload = {
        'type': 'shortcut',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/shortcuts/', data=data)
    assert res.status_code == HTTPStatus.BAD_REQUEST


@mock_dynamodb2
@mock.patch('slack_sdk.web.base_client.BaseClient.api_call', lambda x, *y, **z:...)
def test_shortcut_add_emoji_set():
    models.TeamConf.create_table()
    models.TeamConf('T0000000000', access_token='access_token').save()
    payload = {
        'type': 'shortcut',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
        'callback_id': 'edit_emoji_set',
        'trigger_id': 'trigger_id',
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/shortcuts/', data=data)
    assert res.status_code == HTTPStatus.OK


@mock.patch('app.models.TeamConf.get', get_object)
@mock.patch('slack_sdk.web.base_client.BaseClient.api_call', lambda x, *y, **z:...)
def test_shortcut_edit_emoji_set():
    payload = {
        'type': 'shortcut',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
        'callback_id': 'edit_emoji_set',
        'trigger_id': 'trigger_id',
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/shortcuts/', data=data)
    assert res.status_code == HTTPStatus.OK


@mock.patch('app.models.TeamConf.get', get_object)
@mock.patch('slack_sdk.web.base_client.BaseClient.api_call', lambda x, *y, **z:...)
def test_shortcut_edit_emoji_set():
    payload = {
        'type': 'shortcut',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
        'callback_id': 'edit_emoji_set',
        'trigger_id': 'trigger_id',
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/shortcuts/', data=data)
    assert res.status_code == HTTPStatus.OK


@mock.patch('app.models.TeamConf.get', mock.Mock(side_effect=models.TeamConf.DoesNotExist))
def test_message_team_conf_does_not_exist():
    payload = {
        'type': 'block_actions',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
        'actions': [{
            'action_id': 'mark_as_read',
            'value': 'mark_as_read',
            'type': 'button',
            'action_ts': '1629922346.043279'
        }],
        'container': {
            'type': 'message',
            'message_ts': '1629922334.000700',
            'channel_id': 'channel_id',
        }
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/message/', data=data)
    assert res.status_code == HTTPStatus.BAD_REQUEST


@mock.patch('app.models.TeamConf.get', get_object)
@mock.patch('slack_sdk.web.base_client.BaseClient.api_call', lambda x, *y, **z:...)
def test_message():
    payload = {
        'type': 'block_actions',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
        'actions': [{
            'action_id': 'mark_as_read',
            'value': 'mark_as_read',
            'type': 'button',
            'action_ts': '1629922346.043279'
        }],
        'container': {
            'type': 'message',
            'message_ts': '1629922334.000700',
            'channel_id': 'channel_id',
        }
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/message/', data=data)
    assert res.status_code == HTTPStatus.OK


@mock.patch('app.models.TeamConf.get', mock.Mock(side_effect=models.TeamConf.DoesNotExist))
def test_view_submission_team_conf_does_not_exist():
    payload = {
        'type': 'view_submission',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
        'view': {
            'callback_id': 'edit_emoji_set',
            'state': {
                'values': {
                    'emoji': {
                        'emoji': {
                            'type': 'plain_text_input',
                            'value': 'example'
                        }
                    }
                }
            },
        }
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/view_submission/', data=data)
    assert res.status_code == HTTPStatus.BAD_REQUEST


@mock_dynamodb2
@mock.patch('slack_sdk.WebClient.emoji_list', lambda x: {'emoji': {'example': 'https://emoji.com/example.png'}})
def test_view_submission_add_emoji():
    models.TeamConf.create_table()
    team_conf = models.TeamConf('T0000000000', access_token='access_token')
    team_conf.save()
    payload = {
        'type': 'view_submission',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
        'view': {
            'callback_id': 'edit_emoji_set',
            'state': {
                'values': {
                    'emoji_0': {
                        'emoji_0': {
                            'type': 'plain_text_input',
                            'value': ':example:'
                        }
                    },
                    'emoji_1': {
                        'emoji_1': {
                            'type': 'plain_text_input',
                            'value': None
                        }
                    },
                    'emoji_2': {
                        'emoji_2': {
                            'type': 'plain_text_input',
                            'value': None
                        }
                    }
                }
            },
        }
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/view_submission/', data=data)
    team_conf.refresh()
    assert len(team_conf.emoji_set) == 1
    assert 'example' in team_conf.emoji_set
    assert res.status_code == HTTPStatus.OK


@mock_dynamodb2
@mock.patch('slack_sdk.WebClient.emoji_list', lambda x: {'emoji': {}})
def test_view_submission_add_unregistered_emoji():
    """存在しないemojiを入力したケース
    """
    models.TeamConf.create_table()
    team_conf = models.TeamConf('T0000000000', access_token='access_token')
    team_conf.save()
    payload = {
        'type': 'view_submission',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
        'view': {
            'callback_id': 'edit_emoji_set',
            'state': {
                'values': {
                    'emoji_0': {
                        'emoji_0': {
                            'type': 'plain_text_input',
                            'value': 'example'
                        }
                    },
                    'emoji_1': {
                        'emoji_1': {
                            'type': 'plain_text_input',
                            'value': None
                        }
                    },
                    'emoji_2': {
                        'emoji_2': {
                            'type': 'plain_text_input',
                            'value': None
                        }
                    }
                }
            },
        }
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/view_submission/', data=data)
    team_conf.refresh()
    assert team_conf.emoji_set is None
    assert res.status_code == HTTPStatus.OK
    assert res.json()['errors']['emoji_0'] == '登録されていないemojiです'


@mock_dynamodb2
@mock.patch('slack_sdk.WebClient.emoji_list', lambda x: {'emoji': {}})
def test_view_submission_remove_emoji():
    """emojiを削除"""
    models.TeamConf.create_table()
    team_conf = models.TeamConf('T0000000000', access_token='access_token', emoji_set={'example'})
    team_conf.save()
    payload = {
        'type': 'view_submission',
        'team': {
            'id': 'T0000000000',
            'domain': 'team_domain'
        },
        'user': {
            'id': 'U00XXXXXXX',
            'team_id': 'T0000000000'
        },
        'view': {
            'callback_id': 'edit_emoji_set',
            'state': {
                'values': {
                    'emoji_0': {
                        'emoji_0': {
                            'type': 'plain_text_input',
                            'value': None
                        }
                    },
                    'emoji_1': {
                        'emoji_1': {
                            'type': 'plain_text_input',
                            'value': None
                        }
                    },
                    'emoji_2': {
                        'emoji_2': {
                            'type': 'plain_text_input',
                            'value': None
                        }
                    }
                }
            }
        }
    }
    data = {'payload': json.dumps(payload)}
    res = client.post('/v1/actions/view_submission/', data=data)
    team_conf.refresh()
    assert res.status_code == HTTPStatus.OK
    assert team_conf.emoji_set is None
