import os
from pathlib import Path

from pydantic import BaseSettings, EmailStr


class Config(BaseSettings):
    ENV: str = 'dev'
    DEBUG: bool = True
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    APP_SCHEMA: str = 'http'
    APP_HOST: str = 'localhost'     # хост в Docker
    REMOTE_HOST: str = 'localhost'  # хост для доступа извне
    APP_PORT: int = 8000
    CORS_ALLOWED_ORIGINS: str
    POSTGRES_USER: str = 'user'
    POSTGRES_PASSWORD: str = 'password'
    POSTGRES_PORT: str = 5432
    POSTGRES_DB: str = 'db'
    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 30 * 60
    RESET_PASSWORD_TOKEN_SECRET: str
    VERIFICATION_TOKEN_SECRET: str
    EMAIL_HOST: str
    EMAIL_PORT: int = 465
    EMAIL_HOST_USER: EmailStr
    EMAIL_HOST_PASSWORD: str
    EMAIL_FROM: EmailStr
    EMAIL_FROM_NAME: str
    ADMIN_EMAIL: EmailStr
    ADMIN_PASSWORD: str
    ADMIN_USERNAME: str
    REDIS_HOST_NAME: str = 'redis'
    REDIS_PORT: int = 6379
    REDIS_HOST_PASSWORD: str = ''

    class Config:
        env_file = '.env.dev'
        env_file_encoding = 'utf-8'


class DevelopmentConfig(Config):
    pass


class ProductionConfig(Config):
    DEBUG = False


def get_config():
    env = os.environ.get('ENV', 'dev')
    config_types = {
        'dev': DevelopmentConfig(),
        'prod': ProductionConfig(),
    }
    return config_types.get(env, DevelopmentConfig())


config: Config = get_config()
