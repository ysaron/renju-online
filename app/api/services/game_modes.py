import json

from sqlalchemy.dialects import postgresql as psql
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.game import GameModeSchema
from app.models.game import GameMode
from app.config import config


async def bulk_create_game_modes(db: AsyncSession):
    print('Updating game modes...')
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
    await db.execute(update_stmt)
    await db.commit()
    print('Modes have been updated.')
