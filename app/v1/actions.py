"""
SlackからのInteractiveActionsリクエストを処理する
"""
import enum
import logging
from http import HTTPStatus
from typing import List, Optional

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
            if payload.container.is_view:
                # モーダルからの入力イベントが来るが使わないので空のレスポンスを返す
                print(form['payload'])
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
        blocks = [InputBlock(block_id='emoji_1', label='1つ目のemoji', element=PlainTextInputElement(action_id='emoji_1'))]
        view = View(title='emojiを追加する', type='modal', callback_id='edit_emoji_set', blocks=blocks, submit='送信')
        client.views_open(trigger_id=payload.trigger_id, view=view)
    if payload.callback_id == 'add_emoji':
        blocks = [
            InputBlock(
                block_id='emoji',
                label='追加するemoji',
                element=PlainTextInputElement(action_id='emoji', placeholder=':atodeyomu:'),
            ),
        ]
        view = View(title='emojiを追加する', type='modal', callback_id='add_emoji', blocks=blocks, submit='登録する')
        if payload.trigger_id:
            client.views_open(trigger_id=payload.trigger_id, view=view)
    if payload.callback_id == 'remove_emoji':
        # TODO: TeamConf.emoji_setがNoneの場合を考える
        options = [Option(label=f':{item}:', value=item) for item in team_conf.emoji_set]
        view = View(title='emojiを削除する',
                    type='modal',
                    callback_id='remove_emoji',
                    blocks=[
                        ActionsBlock(
                            block_id='emoji_list',
                            elements=[CheckboxesElement(action_id='emoji_list', options=options)],
                        )
                    ],
                    submit='選択した項目を削除する')
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
    if payload.view.callback_id == 'add_emoji':
        emoji: str = payload.view.state.values['emoji']['emoji']['value'].strip(':')
        # 入力されたemojiがワークスペースに登録されているか検証
        client = WebClient(team_conf.access_token)
        emoji_list = list(client.emoji_list().get('emoji').keys())
        if emoji not in emoji_list:
            return {'response_action': 'errors', "errors": {'emoji': 'ワークスペースに登録されていないemojiです'}}
        if team_conf.emoji_set is None:
            # TeanConfのレコードにemoji_setが存在しない場合Noneが返ってくるので空の`set()`をセットする
            team_conf.emoji_set = set()
        if 10 <= len(team_conf.emoji_set):
            # モーダルに表示できるcheckboxが10個までなので登録できる上限は10個
            return {'response_action': 'errors', "errors": {'emoji': '登録できるemojiは最大10個までです'}}
        team_conf.emoji_set.add(emoji)
        team_conf.save()
    if payload.view.callback_id == 'remove_emoji':
        selected_options = payload.view.state.values['emoji_list']['emoji_list']['selected_options']
        for item in selected_options:
            team_conf.emoji_set.remove(item['value'])
        team_conf.save()
    return Response()
