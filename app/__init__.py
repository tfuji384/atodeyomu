import logging

import sentry_sdk
from fastapi import FastAPI
from mangum import Mangum
from sentry_sdk.integrations.logging import LoggingIntegration

from app.v1 import actions, authorization, events
from app.settings import settings


def before_send(event, hint):
    if settings.ENVIRONMENT_NAME == 'test':
        return None
    return event  # pragma: no cover


sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
sentry_sdk.init(dsn=settings.SENTRY_DNS, integrations=[sentry_logging], before_send=before_send)

app = FastAPI(title='atodeyomu')
if settings.ENVIRONMENT_NAME == 'local':
    app.debug = True

app.include_router(actions.router, prefix='/v1')
app.include_router(authorization.router, prefix='/v1')
app.include_router(events.router, prefix='/v1')
app_handler = Mangum(app)
