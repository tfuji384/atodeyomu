from datetime import datetime
from pytz import timezone

jst = timezone('Asia/Tokyo')


def now() -> datetime:
    return datetime.now(tz=jst)
