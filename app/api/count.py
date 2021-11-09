from fastapi import APIRouter, Depends, HTTPException, Body
from starlette.status import HTTP_400_BAD_REQUEST
from typing import List
from datetime import datetime
# custom defined
from app.models.user import User
from app.core.config import timezone
from app.dependencies.jwt import get_current_user_authorizer
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.crud.count import get_one_count_by_query, update_count_by_query_with_item, get_count_list_by_query

router = APIRouter()


@router.patch('/count', tags=['count'], name='修改计数数据')
async def patch_count(
        case_id: str = Body(...), count: List[str] = Body(None), extra: List[str] = Body(None),
        remark: str = Body(None),
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    data_count = await get_one_count_by_query(conn=db, query={'case_id': case_id})
    if data_count.user_id != user.id:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='非分配本人不可修改')
    item = {}
    if count is not None:
        item['count'] = count
    if extra is not None:
        item['extra'] = extra
    if remark is not None:
        item['remark'] = remark
    item['update_time'] = datetime.now(tz=timezone).isoformat()
    await update_count_by_query_with_item(conn=db, query={'case_id': case_id, 'user_id': user.id}, item=item)
    return {'msg': '修改成功'}


@router.get('/count', tags=['count'], name='获取单个计数数据')
async def get_count(
        case_id: str,
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    data_count = await get_one_count_by_query(conn=db, query={'case_id': case_id})
    if data_count.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='非分配本人不可查看')
    return {'data': data_count}


@router.get('/count/me', tags=['count'], name='获取计数数据')
async def get_count_me(
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    data_count = await get_count_list_by_query(conn=db, query={'user_id': user.id})
    return {'data': data_count}
