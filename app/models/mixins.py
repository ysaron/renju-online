import uuid

from sqlalchemy import Column
from sqlalchemy.dialects import postgresql as psql


class UuidIdMixin:
    id: uuid.UUID = Column(psql.UUID, primary_key=True, unique=True, default=uuid.uuid4)
