from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from app.core.config import database_name, count_collection_name, case_collection_name, analysis_collection_name, \
    user_collection_name
from app.models.case import CaseModel, CaseCreateModel, CaseWithAnalysisAndCount, AnalysisInCase, \
    CountInCase, AnalysisCreateModel, CountCreateModel, CaseWithAnalysisAndCountByUser, AnalysisByUser, CountByUser


async def get_case_list_with_analysis_and_count_by_query(
        conn: AsyncIOMotorClient, query: dict, user_id: str = None, page: int = None, limit: int = None
):
    '''
        参数中user_id有值时为普通用户调用，数量不多，不做分页；user_id为空时为统计调用，数量大需要分页
        TODO 该函数设计失误，原本不应该带有状态，后续可考虑拆开
    '''
    if user_id is not None:
        from app.utils.utils import choose_work_type
        result = conn[database_name][case_collection_name].aggregate([
            {'$lookup': {'from': analysis_collection_name, 'localField': 'case_id', 'foreignField': 'case_id',
                         'as': 'analysis'}},
            {'$lookup': {'from': count_collection_name, 'localField': 'case_id', 'foreignField': 'case_id',
                         'as': 'count'}},
            {'$match': query},
            {'$unwind': '$count'},
            {'$unwind': '$analysis'},
            {'$lookup': {'from': 'user', 'localField': 'analysis.user_id', 'foreignField': 'id',
                         'as': 'analysis.user'}},
            {'$lookup': {'from': 'user', 'localField': 'count.user_id', 'foreignField': 'id', 'as': 'count.user'}},
            {'$unwind': '$analysis.user'},
            {'$unwind': '$count.user'},
            {'$group': {'_id': {'case_id': '$case_id', 'count': '$count', 'finished': '$finished'},
                        'analysis': {'$push': '$analysis'}}},
            {'$sort': {'_id.case_id': 1}}
        ])
        return [CaseWithAnalysisAndCountByUser(
            case_id=x['_id']['case_id'],
            finished=x['_id']['finished'],
            work=choose_work_type(data=x, user_id=user_id),
            analysis=[AnalysisByUser(
                is_main=y['is_main'],
                analysis=y['analysis'],
                karyotype=y['karyotype'],
                user=y['user_id'],
                realname=y['user']['realname'],
                update_time=y['update_time']
            ) for y in x['analysis']],
            count=CountByUser(
                count=x['_id']['count']['count'],
                extra=x['_id']['count']['extra'],
                remark=x['_id']['count']['remark'],
                user=x['_id']['count']['user_id'],
                realname=x['_id']['count']['user']['realname'],
                update_time=x['_id']['count']['update_time']
            )
        ) async for x in result]
    else:
        result = conn[database_name][case_collection_name].aggregate([
            {'$lookup': {'from': analysis_collection_name, 'localField': 'case_id', 'foreignField': 'case_id',
                         'as': 'analysis'}},
            {'$lookup': {'from': count_collection_name, 'localField': 'case_id', 'foreignField': 'case_id',
                         'as': 'count'}},
            {'$unwind': '$count'},
            {'$unwind': '$analysis'},
            {'$match': query},
            {'$lookup': {'from': 'user', 'localField': 'analysis.user_id', 'foreignField': 'id',
                         'as': 'analysis.user'}},
            {'$lookup': {'from': 'user', 'localField': 'count.user_id', 'foreignField': 'id', 'as': 'count.user'}},
            {'$unwind': '$analysis.user'},
            {'$unwind': '$count.user'},
            {'$group': {'_id': {'case_id': '$case_id', 'count': '$count', 'finished': '$finished'},
                        'analysis': {'$push': '$analysis'}}},
            {'$sort': {'_id.case_id': 1}},
            {'$skip': (page - 1) * limit},
            {'$limit': limit}
        ])
        return [CaseWithAnalysisAndCount(
            case_id=x['_id']['case_id'],
            finished=x['_id']['finished'],
            analysis=[AnalysisInCase(
                is_main=y['is_main'],
                analysis=y['analysis'],
                karyotype=y['karyotype'],
                user_id=y['user_id'],
                realname=y['user']['realname'],
                update_time=y['update_time']
            ) for y in x['analysis']],
            count=CountInCase(
                count=x['_id']['count']['count'],
                extra=x['_id']['count']['extra'],
                remark=x['_id']['count']['remark'],
                user_id=x['_id']['count']['user_id'],
                realname=x['_id']['count']['user']['realname'],
                update_time=x['_id']['count']['update_time']
            )
        ) async for x in result]


async def get_case_list_by_query(conn: AsyncIOMotorClient, query: dict):
    result = conn[database_name][case_collection_name].find(query)
    return [CaseModel(**x) async for x in result]


async def create_case_list_with_item(conn: AsyncIOMotorClient, item: List[CaseCreateModel]):
    conn[database_name][case_collection_name].insert_many([x.dict() for x in item])
    return True


async def get_one_case_with_analysis_and_count_by_query(conn: AsyncIOMotorClient, query: dict):
    result = conn[database_name][case_collection_name].aggregate([
        {'$match': query},
        {'$lookup': {'from': analysis_collection_name, 'localField': 'case_id', 'foreignField': 'case_id',
                     'as': 'analysis'}},
        {'$lookup': {'from': count_collection_name, 'localField': 'case_id', 'foreignField': 'case_id', 'as': 'count'}},
        {'$unwind': '$analysis'},
        {'$unwind': '$count'},
        {'$lookup': {'from': user_collection_name, 'localField': 'analysis.user_id', 'foreignField': 'id',
                     'as': 'analysis.user'}},
        {'$unwind': '$analysis.user'},
        {'$lookup': {'from': user_collection_name, 'localField': 'count.user_id', 'foreignField': 'id',
                     'as': 'count.user'}},
        {'$unwind': '$count.user'},
        {'$group': {'_id': {'case_id': '$case_id', 'finished': '$finished', 'count': '$count'},
                    'analysis': {'$push': '$analysis'}}}
    ])
    result = [x async for x in result]
    return CaseWithAnalysisAndCount(
        case_id=result[0]['_id']['case_id'],
        finished=result[0]['_id']['finished'],
        analysis=[AnalysisInCase(
            is_main=x['is_main'],
            analysis=x['analysis'],
            karyotype=x['karyotype'],
            user_id=x['user_id'],
            realname=x['user']['realname'],
            update_time=x['update_time'] if x.get('update_time') else None
        ) for x in result[0]['analysis']],
        count=CountInCase(
            count=result[0]['_id']['count']['count'],
            extra=result[0]['_id']['count']['extra'],
            remark=result[0]['_id']['count']['remark'],
            user_id=result[0]['_id']['count']['user_id'],
            realname=result[0]['_id']['count']['user']['realname'],
            update_time=result[0]['_id']['count']['update_time'] if result[0]['_id']['count'].get(
                'update_time') else None
        )
    )


async def count_case_by_query(conn: AsyncIOMotorClient, query: dict):
    result = await conn[database_name][case_collection_name].count_documents(query)
    return result


async def create_case_with_analysis_and_count(conn: AsyncIOMotorClient, case_item: List[CaseCreateModel],
                                              analysis_item: List[AnalysisCreateModel],
                                              count_item: List[CountCreateModel]):
    conn[database_name][case_collection_name].insert_many([x.dict() for x in case_item])
    conn[database_name][analysis_collection_name].insert_many([x.dict() for x in analysis_item])
    conn[database_name][count_collection_name].insert_many([x.dict() for x in count_item])
    return True
