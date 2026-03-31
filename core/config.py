#core/config.py

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


#class for authentication and configuration of requests that hides the secrets keys
class Settings(BaseSettings):
    SLACK_SIGNING_SECRET: str
    SECRET_KEY: str #for things that not related to slack, like JWT token generation
    ALGORITHM: str = "HS256" #JWT signing algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # JWT expiration in minutes
    VERIFY_SLACK_SIGNATURE: bool = True  # Disable only for local testing
    
    # Business logic configuration
    DAILY_KUDOS_LIMIT: int = 5  # Maximum kudos per user per day
    MAX_KUDOS_MESSAGE_LENGTH: int = 200  # Maximum length for kudos messages
    SLACK_REQUEST_TIMEOUT_SECONDS: int = 300  # 5 minutes - max age for Slack requests

    model_config = ConfigDict(env_file=".env")

settings = Settings()