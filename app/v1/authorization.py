"""OAuth"""
import logging
from http import HTTPStatus
from fastapi.param_functions import Query

from pydantic import BaseModel, parse_obj_as
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from sentry_sdk.integrations.serverless import serverless_function
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.models import TeamConf
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/authorize')


class Team(BaseModel):
    id: str
    name: str


class SlackResponse(BaseModel):
    ok: bool
    app_id: str
    access_token: str
    team: Team


@serverless_function
@router.get('/', response_class=HTMLResponse)
async def authorize(code: str):
    client = WebClient()
    try:
        response = client.oauth_v2_access(
            code=code,
            client_id=settings.SLACK_CLIENT_ID,
            client_secret=settings.SLACK_CLIENT_SECRET,
            redirect_uri='',
        )
    except SlackApiError as e:
        logger.error(e, exc_info=True)
        return HTMLResponse('インストールに失敗しました', status_code=HTTPStatus.BAD_REQUEST)
    slack_response = parse_obj_as(SlackResponse, response.data)
    try:
        team_conf = TeamConf.get(slack_response.team.id)
        team_conf.access_token = slack_response.access_token
        team_conf.save()
    except TeamConf.DoesNotExist:
        TeamConf(slack_response.team.id, access_token=slack_response.access_token).save()
    return HTMLResponse('登録が完了しました')
