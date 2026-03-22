from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    apprise_api_base_url: str = "http://localhost:8000"
