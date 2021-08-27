from datetime import datetime, timedelta, timezone

from freezegun import freeze_time

from app.datetime import now


def test_now():
    with freeze_time('2020-01-01 00:00:00'):
        assert now() == datetime(2020, 1, 1, 9, tzinfo=timezone(timedelta(hours=9)))
