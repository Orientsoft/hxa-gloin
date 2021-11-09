from fastapi import APIRouter, Depends, HTTPException, Body
from starlette.status import HTTP_400_BAD_REQUEST
from typing import List
from datetime import datetime
# custom defined
from app.models.user import User
from app.core.config import timezone
from app.dependencies.jwt import get_current_user_authorizer
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.crud.analysis import get_one_analysis_by_query, update_analysis_by_query_with_item, get_analysis_list_by_query

# from app.models.analysis import AnalysisUpdateModel

router = APIRouter()


@router.patch('/analysis', tags=['analysis'], name='录入分析数据')
async def patch_analysis(
        case_id: str = Body(...), analysis: List[str] = Body(None), karyotype: str = Body(None),
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    data_analysis = await get_one_analysis_by_query(conn=db, query={'case_id': case_id, 'user_id': user.id})
    if not data_analysis:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='非分配用户无法修改')
    item = {}
    if analysis is not None:
        item['analysis'] = analysis
    if karyotype is not None:
        item['karyotype'] = karyotype
    item['update_time'] = datetime.now(tz=timezone).isoformat()
    await update_analysis_by_query_with_item(conn=db, query={'case_id': case_id, 'user_id': user.id}, item=item)
    return {'msg': '提交成功'}


@router.get('/analysis', tags=['analysis'], name='获取单个分析数据')
async def get_analysis(
        case_id: str,
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    data_analysis = await get_one_analysis_by_query(conn=db, query={'case_id': case_id, 'user_id': user.id})
    if data_analysis.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='非分配用户无法修改')
    return {'data': data_analysis}


@router.get('/analysis/me', tags=['analysis'], name='获取分析数据')
async def get_analysis_me(
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    data_analysis = await get_analysis_list_by_query(conn=db, query={'user_id': user.id})
    return {'data': data_analysis}
