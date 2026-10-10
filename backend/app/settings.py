from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TIMELINE_", env_file=".env")

    cors_origins: list[str] = ["http://localhost:5173"]
    max_events: int = 100
    wikimedia_contact: str = "https://github.com/LeCherry35/timeline"
    wikimedia_timeout: float = 20.0
    wikimedia_max_retries: int = 2


settings = Settings()
