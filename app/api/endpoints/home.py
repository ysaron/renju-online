from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.config import config
from .utils import url_for_port

router = APIRouter()


@router.get('/', response_class=HTMLResponse)
async def home(request: Request) -> Jinja2Templates.TemplateResponse:
    template = Jinja2Templates(directory='templates')
    template.env.globals['url_for_port'] = url_for_port
    context = {
        'request': request,
        'app_host': config.APP_HOST,
        'remote_host': config.REMOTE_HOST,
        'app_port': config.APP_PORT,
        'debug': config.DEBUG,
    }
    return template.TemplateResponse('index.html', context=context)
