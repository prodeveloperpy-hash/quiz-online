from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://quiz_user:quiz_password@127.0.0.1:3306/online_quiz"
    secret_key: str = "local-online-quiz-change-before-production-2026"
    access_token_expire_minutes: int = 720
    frontend_url: str = "http://localhost:5173"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_email: str = "fypisp2026@gmail.com"
    smtp_app_password: str = "hzegkjeofqjxigon"
    smtp_from_name: str = "Quiz Online"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
