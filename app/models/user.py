from pydantic import BaseModel
from datetime import datetime
from typing import List
from enum import Enum
# custom defined
from app.utils.security import verify_password
from app.models.common import IDModel, UpdatedAtModel, CreatedAtModel


class UserBase(BaseModel):
    username: str
    is_admin: bool
    realname: str


class UserCreate(UserBase, IDModel, UpdatedAtModel, CreatedAtModel):
    password: str


class UserCreateRequest(UserBase):
    password: str


class User(UserBase):
    id: str
    token: str


class UserInDB(UserBase):
    id: str
    salt: str = ''
    hashed_password: str = ''
    realname: str
    create_time: str
    update_time: str

    def check_password(self, password: str):
        return verify_password(self.salt + password, self.hashed_password)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class TokenPayload(BaseModel):
    id: str
    exp: datetime


class UserListModel(BaseModel):
    id: str
    username: str
    is_admin: bool
    realname: str
    create_time: str


class UserListResponse(BaseModel):
    data: List[UserListModel]
    total: int


class GroupEnum(str, Enum):
    A = 'analysis'
    C = 'count'


class CaseTypeEnum(str, Enum):
    L = 'L'
    G = 'G'


class RoleModel(BaseModel):
    id: str
    group_name: str
    group_type: GroupEnum


class RoleCreateModel(IDModel):
    group_name: str
    group_type: GroupEnum


class RolePatchRequest(BaseModel):
    group_name: str


class DivisionModel(BaseModel):
    id: str
    group_id: str
    user_id: str
    user_name: str = None
    quantities: int
    case_type: CaseTypeEnum


class DivisionCreateModel(IDModel):
    group_id: str
    user_id: str
    quantities: int
    case_type: CaseTypeEnum


class DivisionInRole(BaseModel):
    id: str
    quantities: int
    user_id: str
    realname: str
    case_type: CaseTypeEnum


class RoleWithDivisionModel(BaseModel):
    id: str
    group_name: str
    group_type: str
    division: List[DivisionInRole] = []


class DivisionGroupByGroup(BaseModel):
    group_id: str
    group_name: str
    group_type: GroupEnum
    division: List[DivisionModel]
