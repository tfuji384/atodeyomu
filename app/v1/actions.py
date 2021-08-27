"""
SlackからのInteractiveActionsリクエストを処理する
"""
import enum
import emoji
import logging
from http import HTTPStatus
from typing import Dict, List, Optional

from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, parse_raw_as
from sentry_sdk.integrations.serverless import serverless_function
from slack_sdk import WebClient
from slack_sdk.models.blocks.basic_components import DispatchActionConfig
from slack_sdk.models.views import View
from slack_sdk.models.blocks import ActionsBlock, CheckboxesElement, InputBlock, Option, PlainTextInputElement
from app.dependencies import verify_signature
from app.models import TeamConf

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/actions')


class Type(str, enum.Enum):
    BLOCK_ACTIONS = 'block_actions'
    SHORTCUT = 'shortcut'
    VIEW_SUBMISSION = 'view_submission'


class ContainerType(str, enum.Enum):
    MESSAGE = 'message'
    VIEW = 'view'


class Action(BaseModel):
    action_id: str
    value: str
    type: str
    action_ts: str


class Container(BaseModel):
    type: ContainerType
    message_ts: Optional[str]
    channel_id: Optional[str]

    @property
    def is_view(self) -> bool:
        return self.type == ContainerType.VIEW

    @property
    def is_message(self) -> bool:
        return self.type == ContainerType.MESSAGE


class Team(BaseModel):
    id: str
    domain: str


class User(BaseModel):
    id: str
    team_id: str


class ViewState(BaseModel):
    values: dict


class ActionView(BaseModel):
    state: ViewState
    callback_id: str


class Payload(BaseModel):
    type: Type
    container: Optional[Container]
    trigger_id: Optional[str]
    callback_id: Optional[str]
    team: Team
    user: User

    @property
    def is_view_submission(self) -> bool:
        return self.type == Type.VIEW_SUBMISSION

    @property
    def is_shortcut(self) -> bool:
        return self.type == Type.SHORTCUT

    @property
    def is_block_actions(self) -> bool:
        return self.type == Type.BLOCK_ACTIONS


class ButtonActionPayload(Payload):
    actions: List[Action]


class ViewSubmissionPayload(Payload):
    view: ActionView


@serverless_function
@router.post('/', status_code=HTTPStatus.OK, dependencies=[Depends(verify_signature)])
async def actions(request: Request):
    form = await request.form()
    payload: Payload = parse_raw_as(Payload, form['payload'])
    if payload.is_view_submission:
        # モーダルに入力した内容を送信するイベント
        return RedirectResponse('./view_submission/')
    if payload.is_shortcut:
        print(payload.callback_id)
        # ショートカット（「emojiを追加」「emojiを編集」）を選択したイベント
        return RedirectResponse('./shortcuts/')
    if payload.is_block_actions:
        if payload.container:
            if payload.container.is_message:
                # 「読んだ」ボタンを押したイベント
                return RedirectResponse('./message/')
    return Response()


@router.post(
    '/shortcuts/',
    name='actions_shortcuts',
    status_code=HTTPStatus.OK,
    dependencies=[Depends(verify_signature)],
)
async def shortcuts(request: Request):
    form = await request.form()
    payload = Payload.parse_raw(form['payload'])
    try:
        team_conf = TeamConf.get(payload.team.id)
    except TeamConf.DoesNotExist:
        return Response(status_code=HTTPStatus.BAD_REQUEST)
    client = WebClient(team_conf.access_token)
    if payload.callback_id == 'edit_emoji_set':
        emoji_set = team_conf.emoji_set
        # 登録できるemojiは3つまで
        if emoji_set is None:
            emoji_count = 0
            external_input = 3
            blocks = []
        else:
            emoji_count = len(emoji_set)
            external_input = 3 - emoji_count
            blocks = [
                InputBlock(
                    block_id=f'emoji_{index}',
                    label=f':{item}:',
                    element=PlainTextInputElement(
                        action_id=f'emoji_{index}',
                        initial_value=item,
                        placeholder=':atodeyomu:',
                    ),
                    optional=True,
                ) for index, item in enumerate(emoji_set)
            ]
        blocks += [
            InputBlock(
                block_id=f'emoji_{emoji_count + i}',
                label=f'追加するemoji（{emoji_count + i}つ目）',
                element=PlainTextInputElement(action_id=f'emoji_{emoji_count + i}', placeholder=':atodeyomu:'),
                optional=True,
            ) for i in range(external_input)
        ]
        view = View(title='emojiを追加する', type='modal', callback_id='edit_emoji_set', blocks=blocks, submit='送信')
        if payload.trigger_id:
            client.views_open(trigger_id=payload.trigger_id, view=view)
    return Response()


@router.post('/message/', name='actions_message', status_code=HTTPStatus.OK, dependencies=[Depends(verify_signature)])
async def message(request: Request):
    form = await request.form()
    payload = ButtonActionPayload.parse_raw(form['payload'])
    try:
        team_conf = TeamConf.get(payload.team.id)
    except TeamConf.DoesNotExist:
        return Response(status_code=HTTPStatus.BAD_REQUEST)
    if payload.actions[0].action_id == 'mark_as_read':
        client = WebClient(team_conf.access_token)
        if payload.container:
            channel = payload.container.channel_id
            ts = payload.container.message_ts
            if channel and ts:
                client.chat_delete(channel=channel, ts=ts)
    return Response()


@serverless_function
@router.post(
    '/view_submission/',
    name='actions_views_submission',
    status_code=HTTPStatus.OK,
    dependencies=[Depends(verify_signature)],
)
async def view_submission(request: Request):
    form = await request.form()
    payload = ViewSubmissionPayload.parse_raw(form['payload'])
    try:
        team_conf = TeamConf.get(payload.team.id)
    except TeamConf.DoesNotExist:
        return Response(status_code=HTTPStatus.BAD_REQUEST)
    if payload.view.callback_id == 'edit_emoji_set':
        emojis: Dict[str, str] = {block_id: v[block_id]['value'] for block_id, v in payload.view.state.values.items()}
        client = WebClient(team_conf.access_token)
        slack_registered_emoji_list = list(client.emoji_list().get('emoji').keys())
        unicode_emoji_list = list(map(lambda x: x.strip(':'), emoji.unicode_codes.EMOJI_UNICODE_ENGLISH.keys()))
        available_emoji_list = slack_registered_emoji_list + unicode_emoji_list
        errors = {}
        for key, value in emojis.items():
            if value is None:
                continue
            if value.strip(':') not in available_emoji_list:
                errors[key] = '登録されていないemojiです'
        if len(errors):
            return {'response_action': 'errors', "errors": errors}
        team_conf.emoji_set = set(map(lambda x: x.strip(':'), filter(lambda x: x, list(emojis.values()))))
        team_conf.save()
    return Response()
