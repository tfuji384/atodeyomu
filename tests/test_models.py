from datetime import datetime, timedelta, timezone

from freezegun import freeze_time
from moto import mock_dynamodb2

from app.models import TeamConf


@mock_dynamodb2
@freeze_time('2020-01-01')
def test_create():
    TeamConf.create_table()
    access_token = 'access_token'
    obj = TeamConf('team_id', access_token=access_token)
    obj.save()
    # `TeamConf.access_token.deserialize()`を検証するためDBから再取得する
    obj.refresh()
    utc = timezone(timedelta(0))
    assert obj.created_at == datetime(2020, 1, 1, tzinfo=utc)
    assert obj.access_token == access_token
