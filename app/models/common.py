from datetime import datetime
from pydantic import BaseModel, validator
import uuid
from app.core.config import timezone


class CreatedAtModel(BaseModel):
    create_time: str = None

    @validator("create_time", pre=True, always=True)
    def default_datetime(cls, v, values, **kwargs) -> str:
        return datetime.now(tz=timezone).isoformat()


class UpdatedAtModel(BaseModel):
    update_time: str = None

    @validator("update_time", pre=True, always=True)
    def default_datetime(cls, v, values, **kwargs) -> str:
        return datetime.now(tz=timezone).isoformat()


class IDModel(BaseModel):
    id: str = ''

    @validator("id", pre=True, always=True)
    def default_id(cls, v, values, **kwargs) -> str:
        return v or uuid.uuid1().hex
