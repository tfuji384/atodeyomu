"""SlackのEventSubscriptionを処理する"""
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Response, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sentry_sdk.integrations.serverless import serverless_function
from slack_sdk import WebClient
from slack_sdk.models.blocks import MarkdownTextObject
from slack_sdk.models.blocks.block_elements import ButtonElement
from slack_sdk.models.blocks.blocks import ActionsBlock, SectionBlock

from app.dependencies import verify_signature
from app.models import TeamConf

router = APIRouter(prefix='/events')


class ReactionAddedEventItem(BaseModel):
    type: str
    channel: str
    ts: str


class Event(BaseModel):
    type: str
    user: str
    item: Optional[ReactionAddedEventItem] = None
    reaction: str
    event_ts: str


class EventCallback(BaseModel):
    type: str
    token: str
    challenge: Optional[str] = None
    team_id: Optional[str] = None
    event: Optional[Event] = None


@serverless_function
@router.post('/', status_code=HTTPStatus.OK, dependencies=[Depends(verify_signature)])
async def events(event: EventCallback):
    if event.type == 'url_verification':
        # AppにRequest URLを登録した際に初回だけ送信されるURLの検証
        # ref: https://api.slack.com/events/url_verification
        return JSONResponse({'challenge': event.challenge})
    try:
        team_conf = TeamConf.get(event.team_id)
    except TeamConf.DoesNotExist:
        return Response(status_code=HTTPStatus.BAD_REQUEST)
    client = WebClient(team_conf.access_token)
    if event.event:
        if event.event.type == 'reaction_added':
            # 投稿にemojiでリアクションがあったイベントを処理する
            # ref: https://api.slack.com/events/reaction_added
            if event.event.reaction in team_conf.emoji_set:
                # リアクションのemojiが設定されている場合
                if event.event.item:
                    item = event.event.item
                    url = client.chat_getPermalink(channel=item.channel, message_ts=item.ts).get('permalink')
                    blocks = [
                        SectionBlock(text=MarkdownTextObject(text=f'<{url}>')),
                        ActionsBlock(
                            elements=[ButtonElement(text='読んだ', action_id='mark_as_read', value='mark_as_read')])
                    ]
                    client.chat_postMessage(text=url, channel=event.event.user, unfurl_links=True, blocks=blocks)
    return Response()
