from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import FileResponse
from starlette.status import HTTP_400_BAD_REQUEST
from typing import List
import pandas as pd
import logging
import time
import os
# custom defined
from app.models.user import User
from app.models.case import CaseCreateModel, CaseImportRequest
from app.dependencies.jwt import get_current_user_authorizer
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.crud.case import get_case_list_with_analysis_and_count_by_query, get_case_list_by_query, \
    create_case_list_with_item, get_one_case_with_analysis_and_count_by_query, count_case_by_query
from app.crud.user import get_one_user_by_query
from app.core.config import api_key, export_path

from app.crud.analysis import get_analysis_list_by_query
from app.crud.count import get_one_count_by_query

router = APIRouter()


@router.post('/case/import', tags=['case', 'admin'], name='样本数据入口')
async def post_case_import(
        data: List[CaseImportRequest] = Body(...), case_id: str = Body(...), API_KEY: str = Body(...),
        db: AsyncIOMotorClient = Depends(get_database)
):
    # data里只会有一个样本，暂时排除重复排序的情况
    # TODO 有可能会重复导入，所以需要考虑冥等性
    if API_KEY != api_key:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='wrong key')
    data_case = await get_case_list_by_query(conn=db, query={'case_id': case_id})
    if data_case:
        logging.info('Case Import Debug: 已有数据')
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='已有数据')
    # 创建case表
    await create_case_list_with_item(conn=db, item=[CaseCreateModel(
        case_id=x.case_id,
    ) for x in data])
    # 创建analysis表，附带分配工作


@router.get('/case/list', tags=['case'], name='获取样本列表')
async def get_case_list(
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    # 筛选count或analysis中该用户拥有权限的case
    data_case = await get_case_list_with_analysis_and_count_by_query(conn=db, user_id=user.id, query={
        '$or': [{'count.user_id': user.id}, {'analysis.user_id': user.id}],
        'finished': False
    })
    # return_obj = []
    # work = None
    # for x in data_case:
    #     if x['count']['user_id'] == user.id:
    #         work = 'C'
    #     else:
    #         for y in x['analysis']:
    #             if y['user_id'] == user.id and y['is_main'] is True:
    #                 work = 'MA'
    #             elif y['user_id'] == user.id and y['is_main'] is False:
    #                 work = 'SA'
    #     analysis = []
    #     for y in x['analysis']:
    #         data_user = await get_one_user_by_query(conn=db, query={'id': y['user_id']})
    #         analysis.append({
    #             'id': y['id'],
    #             'is_main': y['is_main'],
    #             'karyotype': y['karyotype'],
    #             'user': y['user_id'],
    #             'analysis': y['analysis'],
    #             'realname': data_user['realname']
    #         })
    #     return_obj.append({
    #         'id': x['id'],
    #         'case_id': x['case_id'],
    #         'analysis': analysis,
    #         'count': {
    #             'id': x['count']['id'],
    #             'count': x['count']['count'],
    #             'extra': x['count']['extra'],
    #             'user': x['count']['user_id'],
    #             'remark': x['count']['remark']
    #         },
    #         'work': work
    #     })
    return data_case


@router.get('/case/total', tags=['case'], name='样本数据汇总')
async def get_case_total(
        finished: bool = True, page: int = 1, limit: int = 20,
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    data_case = await get_case_list_with_analysis_and_count_by_query(conn=db, query={'finished': finished}, page=page,
                                                                     limit=limit)
    total = await count_case_by_query(conn=db, query={'finished': finished})
    return {'data': data_case, 'total': total}


@router.post('/case/export', tags=['admin'], name='导出样本汇总数据')
async def post_case_export(
        case_list: List[str] = Body(..., embed=True),
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    if not user.is_admin:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='权限不足')
    export_list = []
    error_list = []
    excel_data = {'编号': [], '分析1': [], '分析2': [], '分析3': [], '分析4': [], '分析5': [], '核型1': [], '核型1-主看者': [], '主看时间': [],
                  '核型2': [], '核型2-辅看者': [], '辅看时间': [], '计数1': [], '计数2': [], '计数3': [], '计数4': [], '计数5': [],
                  '计数6': [], '计数7': [], '计数8': [], '计数9': [], '计数10': [], '计数11': [], '计数12': [], '计数13': [],
                  '计数14': [], '计数15': [], '计数者': [], '计数时间': [], '计数备注': []}
    # 需要检查主辅分析是否填完，分析结果是否一致，计数是否15个完整
    for case_id in case_list:
        status = True
        data_case = await get_one_case_with_analysis_and_count_by_query(conn=db, query={'case_id': case_id})
        # 先判断是否完成填写
        for x in data_case.analysis:
            if x.is_main is True and len(x.analysis) != 3:
                error_list.append({'case_id': data_case.case_id, 'error': '未完成主分析'})
                status = False
                # raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='未完成主分析')
            elif x.is_main is False and len(x.analysis) != 2:
                error_list.append({'case_id': data_case.case_id, 'error': '未完成辅分析'})
                status = False
                # raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='未完成辅分析')
        if data_case.analysis[0].karyotype != data_case.analysis[1].karyotype:
            error_list.append({'case_id': data_case.case_id, 'error': '主辅分析结果不一致'})
            status = False
            # raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='主辅分析结果不一致')
        if len(data_case.count.count) != 15:
            error_list.append({'case_id': data_case.case_id, 'error': '未完成计数'})
            status = False
            # raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='未完成计数')
        for x in data_case.analysis:
            if status is True and x.is_main is True:
                excel_data['分析1'].append(x.analysis[0])
                excel_data['分析2'].append(x.analysis[1])
                excel_data['分析3'].append(x.analysis[2])
                excel_data['核型1'].append(x.karyotype)
                excel_data['核型1-主看者'].append(x.realname)
                excel_data['主看时间'].append(x.update_time)
            elif status is True and x.is_main is False:
                excel_data['分析4'].append(x.analysis[0])
                excel_data['分析5'].append(x.analysis[1])
                excel_data['核型2'].append(x.karyotype)
                excel_data['核型2-辅看者'].append(x.realname)
                excel_data['辅看时间'].append(x.update_time)
        if status is True:
            export_list.append(data_case.case_id)
            excel_data['编号'].append(data_case.case_id)
            # 组装15个计数
            for n in range(len(data_case.count.count)):
                excel_data[f'计数{n + 1}'].append(data_case.count.count[n])
            excel_data['计数者'].append(data_case.count.realname)
            excel_data['计数时间'].append(data_case.count.update_time)
            excel_data['计数备注'].append(data_case.count.remark)
    df = pd.DataFrame(excel_data)
    filename = str(time.time()).split('.')[0]
    df.to_excel(f'{export_path}/{filename}.xlsx')
    return {'success': export_list, 'error': error_list, 'file': f'{filename}.xlsx'}


@router.get('/case/export', tags=['admin'], name='下载导出文件')
async def get_case_export(
        filename: str,
        user: User = Depends(get_current_user_authorizer(required=True))
):
    if not os.path.exists(f'{export_path}/{filename}'):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='未找到该文件')
    try:
        headers = {'content-type': 'application/vnd.ms-excel'}
        return FileResponse(path=f'{export_path}/{filename}', headers=headers, filename=filename)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='文件下载异常')



@router.get('/case/info', tags=['case'], name='查询一条样本信息')
async def get_count(
        case_id: str,
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    data_analysis = await get_analysis_list_by_query(conn=db, query={'case_id': case_id})    
    data_count = await get_one_count_by_query(conn=db, query={'case_id': case_id})
    return {'analysis': data_analysis,'count':data_count}