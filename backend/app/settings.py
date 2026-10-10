from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TIMELINE_", env_file=".env")

    cors_origins: list[str] = ["http://localhost:5173"]
    max_events: int = 100


settings = Settings()
