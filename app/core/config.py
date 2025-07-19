import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    APP_PORT: int

    SESSION_MIDDLEWARE_SECRET: str
    JWT_SECRET: str

    GOOGLE_OAUTH_CLIENT_ID: str
    GOOGLE_OAUTH_SECRET: str

    REDIS_HOST: str
    REDIS_PORT: int

    PG_HOST: str
    PG_PORT: int
    PG_USER: str
    PG_PW: str
    PG_DB: str

    PERPLEXITY_API_KEY: str
    OPENAI_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(__file__),
            ".env",
        )
    )


setting = Setting()  # type: ignore
