import os

from pydantic import BaseSettings, EmailStr


class Config(BaseSettings):
    ENV: str = 'dev'
    DEBUG: bool = True
    APP_HOST: str = 'localhost'
    APP_PORT: int = 8000
    POSTGRES_USER: str = 'user'
    POSTGRES_PASSWORD: str = 'password'
    POSTGRES_PORT: str = 5432
    POSTGRES_DB: str = 'db'
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
