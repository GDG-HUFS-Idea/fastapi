import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    SESSION_MIDDLEWARE_SECRET: str
    JWT_SECRET: str

    GOOGLE_OAUTH_CLIENT_ID: str
    GOOGLE_OAUTH_SECRET: str

    PG_USER: str
    PG_PW: str

    PERPLEXITY_API_KEY: str
    OPENAI_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(__file__),
            ".env",
        )
    )


env = Setting()  # type: ignore
