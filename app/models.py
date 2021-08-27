from typing import Any

from cryptography.fernet import Fernet
from pynamodb import attributes, models, types

from app.datetime import now
from app.settings import settings


class EncryptedStringAttribute(attributes.Attribute):
    """文字列を暗号化して参照時に復号するAttribute"""
    attr_type = types.BINARY

    def serialize(self, value: str):
        fernet = Fernet(settings.ENCRYPTION_KEY.encode('utf-8'))
        return fernet.encrypt(value.encode('UTF-8'))

    def deserialize(self, value):
        fernet = Fernet(settings.ENCRYPTION_KEY.encode('utf-8'))
        return fernet.decrypt(value).decode()


class TeamConf(models.Model):
    """Slackのチームごとの設定を保存するモデル
    """
    team_id = attributes.UnicodeAttribute(hash_key=True)  # Slackのワークスペースのteam_id
    access_token = EncryptedStringAttribute()
    emoji_set = attributes.UnicodeSetAttribute()  # SlackAppが反応するリアクションのemojiのset
    created_at = attributes.UTCDateTimeAttribute(default_for_new=now)

    class Meta:
        region = 'ap-northeast-1'
        table_name = settings.DYNAMODB_TABLE
