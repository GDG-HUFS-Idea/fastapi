import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    app_port: int = 80

    pg_host: str = ""
    pg_port: int = 5432
    pg_user: str = ""
    pg_pw: str = ""
    pg_db: str = ""

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(__file__),
            ".env",
        )
    )


env = Setting()
