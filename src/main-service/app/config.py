from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

class Settings(BaseSettings):
    IO_SERVICE_HOST: str
    IO_SERVICE_PORT: int

    @computed_field
    @property
    def IO_SERVICE_URL(self) -> str:
        return f"http://{self.IO_SERVICE_HOST}:{self.IO_SERVICE_PORT}"

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()