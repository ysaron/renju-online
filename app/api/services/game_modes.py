import json
from contextlib import asynccontextmanager

from sqlalchemy.dialects import postgresql as psql

from app.core.db.deps import get_async_session
from app.schemas.game import GameModeSchema
from app.models.game import GameMode
from app.config import config

get_async_session_context = asynccontextmanager(get_async_session)


async def bulk_create_game_modes():
    print('Updating game modes...')
    async with get_async_session_context() as session:
        data_file = config.BASE_DIR / 'data' / 'game_modes.json'
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        modes = [GameModeSchema(**m) for m in data]

        # Upsert: новые моды запишутся, существующие - обновятся
        insert_stmt = psql.insert(GameMode.__table__).values([m.dict() for m in modes])
        update_cols = {col.name: col for col in insert_stmt.excluded}
        update_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[GameMode.id],
            set_=update_cols,
        )
        await session.execute(update_stmt)
        await session.commit()
        print('Modes have been updated.')
