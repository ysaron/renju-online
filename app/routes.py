from fastapi import APIRouter

from .auth.endpoints import auth_router, users_router
from .api.endpoints.common import router as common_router
from .api.endpoints.home import router as home_router
from .api.endpoints.ws import router as ws_router


routes = APIRouter()

routes.include_router(auth_router, tags=['auth'], prefix='/auth')
routes.include_router(users_router, tags=['users'], prefix='/users')
routes.include_router(common_router, tags=['games'])
routes.include_router(home_router, tags=['home'])
routes.include_router(ws_router, tags=['ws_apps'])
