import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.anyio
async def test_example(async_client: AsyncClient, async_session: AsyncSession):
    response = await async_client.get('/')
    assert response.status_code == status.HTTP_200_OK
    assert False



