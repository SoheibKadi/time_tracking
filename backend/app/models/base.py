import uuid
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()
