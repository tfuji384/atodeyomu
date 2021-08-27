from fastapi import Request
from app import app
from app.settings import settings

from app.dependencies import verify_signature


def override_verify_signature(request: Request):
    return True


app.dependency_overrides[verify_signature] = override_verify_signature  # 署名の検証をスキップする
settings.ENVIRONMENT_NAME = 'test'
