from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./pvr.db"
    JWT_SECRET: str 
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None          # your-email@gmail.com
    SMTP_PASSWORD: str | None = None      # 16-character App Password
    SMTP_FROM_NAME: str = "PVR Cinemas"
    FRONTEND_URL: str = "http://localhost:5173"
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()