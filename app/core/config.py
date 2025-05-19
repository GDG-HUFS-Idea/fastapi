import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    app_port: int

    session_middleware_secret: str
    jwt_secret: str

    google_oauth_client_id: str
    google_oauth_secret: str

    frontend_redirect_url: str

    redis_host: str
    redis_port: int

    pg_host: str
    pg_port: int
    pg_user: str
    pg_pw: str
    pg_db: str
    pg_host: str
    pg_port: int
    pg_user: str
    pg_pw: str
    pg_db: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            ".env",
        )
    )


env = Setting()  # type: ignore
