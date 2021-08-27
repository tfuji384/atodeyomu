from http import HTTPStatus

from fastapi import HTTPException, Request
from slack_sdk.signature import SignatureVerifier

from app.settings import settings


async def verify_signature(request: Request) -> bool:
    # リクエストの署名を検証
    # ref: https://api.slack.com/authentication/verifying-requests-from-slack
    verifier = SignatureVerifier(settings.SLACK_SIGNING_SECRET)
    if verifier.is_valid_request(await request.body(), dict(request.headers)):
        return True
    raise HTTPException(HTTPStatus.FORBIDDEN)
