from pydantic import BaseModel
from typing import List
from app.models.common import IDModel, CreatedAtModel, UpdatedAtModel


class CountModel(BaseModel):
    case_id: str
    count: List[str] = None
    extra: List[str] = None
    remark: str = None
    user_id: str
    user_name: str = None


class CountCreateModel(CountModel, IDModel, CreatedAtModel, UpdatedAtModel):
    pass
