from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./pvr.db"
    JWT_SECRET: str 

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()