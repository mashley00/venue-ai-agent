from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    google_maps_api_key: str | None = Field(default=None, alias="GOOGLE_MAPS_API_KEY")
    yelp_api_key: str | None = Field(default=None, alias="YELP_API_KEY")
    database_url: str = Field(default="sqlite:///./local.db", alias="DATABASE_URL")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int | None = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_pass: str | None = Field(default=None, alias="SMTP_PASS")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
