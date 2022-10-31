from fastapi import APIRouter

from .core.users.manager import fa_users, auth_backend
from .schemas.user import UserRead, UserCreate, UserUpdate
from .api.endpoints.common import router as common_router
from .api.endpoints.home import router as home_router


routes = APIRouter()
routes.include_router(
    fa_users.get_auth_router(auth_backend, requires_verification=True),    # требует user.is_verified=True
    prefix='/auth',
    tags=['auth'],
)
routes.include_router(
    fa_users.get_register_router(UserRead, UserCreate),
    prefix='/auth',
    tags=['auth'],
)
routes.include_router(
    fa_users.get_verify_router(UserRead),
    prefix='/auth',
    tags=['auth'],
)
routes.include_router(
    fa_users.get_reset_password_router(),
    prefix='/auth',
    tags=['auth'],
)
routes.include_router(
    fa_users.get_users_router(UserRead, UserUpdate, requires_verification=True),
    prefix='/users',
    tags=['users'],
)

routes.include_router(
    common_router,
    tags=['games'],
)

routes.include_router(home_router, tags=['home'])
