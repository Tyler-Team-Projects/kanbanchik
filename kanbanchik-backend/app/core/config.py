from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "Kanbanchik"
    debug: bool = False
    secret_key: str
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()