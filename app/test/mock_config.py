import types


class MockSetting:
    app_port = 8000
    session_middleware_secret = "test_secret_key"
    google_oauth_client_id = "test_client_id"
    google_oauth_secret = "test_secret"
    google_oauth_callback_uri = "http://localhost:8000/auth/callback/google"
    frontend_redirect_url = "http://localhost:3000"
    redis_host = "localhost"
    redis_port = 6379
    pg_host = "localhost"
    pg_port = 5432
    pg_user = "test_user"
    pg_pw = "test_password"
    pg_db = "test_db"


mock_config_module = types.ModuleType("app.core.config")
mock_config_module.env = MockSetting()  # type: ignore
mock_config_module.Setting = MockSetting  # type: ignore


def register_mock_env():
    import sys

    sys.modules["app.core.config"] = mock_config_module
