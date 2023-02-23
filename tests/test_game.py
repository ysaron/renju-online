import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.game import GameModeInGameSchema, GameCreateSchema
from app.models.user import User
from app.enums.game import PlayerRoleEnum
from app.api.services.games import GameService


class TestGameService:

    @pytest.mark.anyio
    async def test_public_game_creation(
            self,
            async_session: AsyncSession,
            modes_public: list[GameModeInGameSchema],   # список с одним модом "Trinity"
            test_user: User,
    ):
        game_data = GameCreateSchema(modes=modes_public)
        game_meta = await GameService(async_session).create_game(creator=test_user, game_data=game_data)
        assert not game_meta.game.is_private
        assert game_meta.game.num_players == 3, 'мод Trinity подразумевает 3 игрока'
        assert game_meta.game.board_size == 30, 'мод Trinity подразумевает поле 30 x 30'
        assert not game_meta.game.with_myself
        assert len(game_meta.game.players) == 1, 'с только что созданной игрой должен ассоциироваться ровно 1 user'
        assert game_meta.game.players[0].player.name == test_user.name, 'имена автора игры и 1-го игрока не совпадают'
        assert game_meta.game.players[0].role == PlayerRoleEnum.first, 'автор игры должен быть записан 1-м игроком'

    @pytest.mark.anyio
    async def test_game_list(
            self,
            async_session: AsyncSession,
            modes_public: list[GameModeInGameSchema],
            modes_private: list[GameModeInGameSchema],
            test_user: User,
    ):
        for game_data in [
            GameCreateSchema(modes=modes_public),
            GameCreateSchema(modes=modes_private),
            GameCreateSchema(is_private=True, modes=modes_public),
        ]:
            await GameService(async_session).create_game(creator=test_user, game_data=game_data)

        games = await GameService(async_session).get_available_games()
        assert len(games) == 1, 'в список доступных попала приватная игра'
        assert games[0].num_players == 3
