import asyncio
import platform

from app.api.services.game_modes import bulk_create_game_modes


if __name__ == '__main__':
    if platform.system() == 'Windows':
        # во избежание "RuntimeError: Event loop is closed"
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(bulk_create_game_modes())
