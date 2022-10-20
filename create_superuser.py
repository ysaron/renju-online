import asyncio
import platform

from app.core.users.utils import create_user
from app.config import config


if __name__ == '__main__':
    if platform.system() == 'Windows':
        # во избежание "RuntimeError: Event loop is closed"
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_user(
        email=config.ADMIN_EMAIL,
        password=config.ADMIN_PASSWORD,
        name=config.ADMIN_USERNAME,
        is_superuser=True,
        is_verified=True,
    ))
