from os import environ
from pydantic import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT_NAME: str = environ['ENVIRONMENT_NAME']
    DYNAMODB_TABLE: str = environ['DYNAMODB_TABLE']
    SENTRY_DNS: str = environ['SENTRY_DNS']
    SLACK_SIGNING_SECRET: str = environ['SLACK_SIGNING_SECRET']
    SLACK_CLIENT_ID: str = environ['SLACK_CLIENT_ID']
    SLACK_CLIENT_SECRET = environ['SLACK_CLIENT_SECRET']
    ENCRYPTION_KEY = environ['ENCRYPTION_KEY']


settings = Settings()
