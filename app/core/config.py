from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./pvr.db"
    JWT_SECRET: str 
    SMTP_USER: str | None = None         
    RESEND_API_KEY: str | None = None      
    SMTP_FROM_NAME: str = "Chennai Cinemas"
    FRONTEND_URL: str = "http://localhost:3000"
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()