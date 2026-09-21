from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://quiz_user:quiz_password@localhost:3306/online_quiz"
    secret_key: str = "change-this-secret"
    access_token_expire_minutes: int = 720
    frontend_url: str = "http://localhost:5173"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_email: str = ""
    smtp_app_password: str = ""
    smtp_from_name: str = "Quiz Online"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
