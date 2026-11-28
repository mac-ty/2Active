"""
Application configuration.

Loads and validates required settings from environment variables
and the .env file. Provides a centralized configuration object
for database, security, email, and frontend settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    brevo_api_key: str
    session_secret: str
    frontend_origin: str
    brevo_sender_email: str
    brevo_sender_name: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()