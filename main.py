import uvicorn
from fastapi import FastAPI

from app.routes import routes
from app.config import config

app = FastAPI()

app.include_router(routes)


if __name__ == '__main__':
    uvicorn.run('main:app', host=config.APP_HOST, port=config.APP_PORT, reload=True)
