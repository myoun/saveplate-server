from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str
    DB_USER: str
    DB_PW: str
    SECRET_KEY: str

    class Config:
        env_file = '.env'

settings = Settings()