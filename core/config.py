from pydantic_settings import BaseSettings

#class for authentication and configuration of requests that hides the secrets keys
class Settings(BaseSettings):
    SLACK_SIGNING_SECRET: str
    SECRET_KEY: str #for things that not related to slack, like JWT token generation
    ALGORITHM: str = "HS256" #JWT signing algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # JWT expiration in minutes

    class Config:
        env_file = ".env"

settings = Settings()