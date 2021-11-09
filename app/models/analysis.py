from pydantic import BaseModel
from typing import List
from app.models.common import IDModel, CreatedAtModel, UpdatedAtModel


class AnalysisModel(BaseModel):
    case_id: str
    is_main: bool
    analysis: List[str] = None
    karyotype: str = None
    user_id: str
    user_name: str = None


class AnalysisCreateModel(AnalysisModel, IDModel, UpdatedAtModel, CreatedAtModel):
    pass
