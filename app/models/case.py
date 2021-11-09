from pydantic import BaseModel
from typing import List
from enum import Enum
from app.models.common import IDModel, CreatedAtModel, UpdatedAtModel


class TaskEnum(str, Enum):
    A = 'analysis'
    C = 'count'


class AnalysisInModel(BaseModel):
    is_main: bool
    analysis: List[str]
    karyotype: str
    user_id: str
    username: str


class CountInModel(BaseModel):
    count: List[str]
    extra: List[str]
    remark: str
    user_id: str
    username: str


class CaseModel(BaseModel):
    case_id: str
    finished: bool


class CaseImportRequest(BaseModel):
    case_id: str


class CaseCreateModel(IDModel, CreatedAtModel, UpdatedAtModel):
    case_id: str
    finished: bool = False


class AnalysisCreateModel(IDModel, CreatedAtModel, UpdatedAtModel):
    case_id: str
    is_main: bool
    analysis: List[str] = []
    karyotype: str = None
    user_id: str
    user_name: str = None


class CountCreateModel(IDModel, CreatedAtModel, UpdatedAtModel):
    case_id: str
    count: list = []
    extra: list = []
    remark: str = None
    user_id: str
    user_name: str = None


class AnalysisInCase(BaseModel):
    is_main: bool
    analysis: list = []
    karyotype: str = None
    user_id: str
    realname: str
    update_time: str = None


class CountInCase(BaseModel):
    count: list = []
    extra: list = []
    remark: str = None
    user_id: str
    realname: str
    update_time: str = None


class CaseWithAnalysisAndCount(BaseModel):
    case_id: str
    finished: bool
    analysis: List[AnalysisInCase]
    count: CountInCase


class AnalysisByUser(BaseModel):
    is_main: bool
    analysis: list = []
    karyotype: str = None
    user: str
    realname: str
    update_time: str = None


class CountByUser(BaseModel):
    count: list = []
    extra: list = []
    remark: str = None
    user: str
    realname: str
    update_time: str = None


class WorkEnum(str, Enum):
    C = 'C'
    MA = 'MA'
    SA = 'SA'


class CaseWithAnalysisAndCountByUser(BaseModel):
    case_id: str
    finished: bool
    analysis: List[AnalysisByUser]
    count: CountByUser
    work: WorkEnum
