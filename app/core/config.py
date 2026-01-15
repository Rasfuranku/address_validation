from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    SMARTY_AUTH_ID: str = ""
    SMARTY_AUTH_TOKEN: str = ""
    SMARTY_WEBSITE_DOMAIN: str = "http:localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
