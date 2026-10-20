from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    upi_id: str
    upi_payee_name: str
    admin_payment_review_key: str
    app_base_url: str = "http://localhost:8000"
    cron_secret: str 
    currency: str = "INR"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
