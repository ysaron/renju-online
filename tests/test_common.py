import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.anyio
async def test_main(async_client: AsyncClient):
    response = await async_client.get('/')
    assert response.status_code == status.HTTP_200_OK
    assert 'text/html' in response.headers['content-type'], 'Корневой URL не вернул HTML-страницу'
