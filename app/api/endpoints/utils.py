from urllib import parse
from typing import Any

from fastapi import Request

from app.config import config


def url_for_port(request: Request, name: str, **path_params: Any) -> str:
    """ Модификация url_for. Добавляет APP_PORT к результирующему url """
    url = request.url_for(name, **path_params)
    parsed = list(parse.urlparse(url))
    if config.APP_PORT != 8000:
        parsed[1] = f'{parsed[1]}:{config.APP_PORT}'
    return parse.urlunparse(parsed)
