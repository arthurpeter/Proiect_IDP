from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Settings(BaseSettings):
    IO_SERVICE_HOST: str = "io-service"
    IO_SERVICE_PORT: int = 8000

    JWT_SECRET_KEY: str = "remailder-super-secret-jwt-key-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    @computed_field
    @property
    def IO_SERVICE_URL(self) -> str:
        return f"http://{self.IO_SERVICE_HOST}:{self.IO_SERVICE_PORT}"

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')


settings = Settings()
