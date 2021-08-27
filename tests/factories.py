from datetime import datetime
from typing import Optional, Set
from app.models import TeamConf


def get_object(team_id: str):
    return TeamConfFactory()


class TeamConfFactory:
    def __init__(
        self,
        team_id: Optional[str] = 'T0000000000',
        access_token: Optional[str] = 'xoxb-0000000000000-0000000000000-aaaaaaaaaaaaaaaaaaaaaaaa',
        emoji_set: Optional[Set[str]] = None,
        *args,
        **kwargs,
    ):
        self.team_id = team_id
        self.access_token = access_token
        self.emoji_set = emoji_set or {'atodeyomu'}

    created_at: datetime = datetime(2021, 8, 1)
