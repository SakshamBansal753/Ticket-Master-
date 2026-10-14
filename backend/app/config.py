from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_payment_link: str = ""
    app_base_url: str = "http://localhost:8000"
    cron_secret: str = "change-me"
    currency: str = "inr"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
