from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

class Settings(BaseSettings):
    IO_SERVICE_HOST: str
    IO_SERVICE_PORT: int

    RABBITMQ_USER: str
    RABBITMQ_PASS: str
    RABBITMQ_HOST: str

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    SMTP_SENDER: str

    @computed_field
    @property
    def IO_SERVICE_URL(self) -> str:
        return f"http://{self.IO_SERVICE_HOST}:{self.IO_SERVICE_PORT}"
    
    @computed_field
    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}/"

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()