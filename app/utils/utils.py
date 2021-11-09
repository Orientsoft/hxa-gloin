from fastapi import Depends
from datetime import datetime
from app.core.config import src_path, src_ext
from app.crud.case import get_case_list_by_query, create_case_with_analysis_and_count
from app.crud.user import get_all_division_group_by_group
from app.models.case import CaseCreateModel, AnalysisCreateModel, CountCreateModel, WorkEnum
from app.db.mongodb import get_database
import os
import traceback


def choose_work_type(data, user_id):
    if data['_id']['count']['user_id'] == user_id:
        return WorkEnum.C
    else:
        for y in data['analysis']:
            if y['user_id'] == user_id and y['is_main'] is True:
                return WorkEnum.MA
            elif y['user_id'] == user_id and y['is_main'] is False:
                return WorkEnum.SA
        else:
            return None


def month_path():
    now = datetime.now()
    path = now.strftime('%y%m')

    return path


async def scan_files_by_path():
    # 先扫描目标路径下文件，筛选组装case_id列表，新的case进行判断并直接分配分析计数
    m_path = month_path()
    db = await get_database()
    # 此时文件带sample_id，例如L2104052638.045.MMI
    filenames = [filename for filename in os.listdir(os.path.join(src_path, m_path)) if src_ext in filename]
    # 只保留case_id
    filenames = sorted(list(set(x.split('.')[0] for x in filenames)))
    data_case = await get_case_list_by_query(conn=db, query={})
    scaned_filenames = [x.case_id for x in data_case]
    # 取差集筛选未扫描文件
    new_cases = list(set(filenames).difference(set(scaned_filenames)))
    data_division = await get_all_division_group_by_group(conn=db)
    # data_division = [
    #     {
    #         "group_id": "group_id",
    #         "group_name": "group_name",
    #         "group_type": "count",
    #         "division": [
    #             {
    #                 'user_id': '$user_id',
    #                 'user_name': '$user.realname',
    #                 'quantities': '$quantities',
    #                 'case_type': 'L',
    #                 'group_id': '$group_id',
    #                 'id': '$id'
    #             },
    #             {
    #                 'user_id': '$user_id',
    #                 'user_name': '$user.realname',
    #                 'quantities': '$quantities',
    #                 'case_type': 'L',
    #                 'group_id': '$group_id',
    #                 'id': '$id'
    #             }
    #         ]
    #     }
    # ]
    division = {'L': {'analysis': [], 'count': []}, 'G': {'analysis': [], 'count': []}}
    case_insert_list = []
    analysis_insert_list = []
    count_insert_list = []
    # 组装分工
    # {
    #     'L': {
    #         'analysis': [
    #             {'group_name': '分析A组', 'division': [
    #                 {'user_id': 'xxx', 'quantities': 20},
    #                 {'user_id': 'yyy', 'quantities': 20}
    #             ]}
    #         ],
    #         'count': [
    #             {'user_id': 'xxx', 'quantities': 20, 'group_name': '计数A组'}
    #         ]
    #     }
    # }
    for x in data_division:
        for y in x.division:
            if x.group_type == 'count':
                division[y.case_type][x.group_type].append(
                    {
                        'user_id': y.user_id,
                        'user_name': y.user_name,
                        'quantities': y.quantities,
                        'group_name': x.group_name
                    }
                )
            else:
                for z in division[y.case_type][x.group_type]:
                    if x.group_name == z['group_name']:
                        z['division'].append(
                            {
                                'user_id': y.user_id,
                                'user_name': y.user_name,
                                'quantities': y.quantities
                            }
                        )
                        break
                else:
                    division[y.case_type][x.group_type].append(
                        {
                            'group_name': x.group_name,
                            'division': [
                                {
                                    'user_id': y.user_id,
                                    'user_name': y.user_name,
                                    'quantities': y.quantities
                                }
                            ]
                        }
                    )
    # 对analysis和count根据group_name进行排序, group_name都在value下同层
    for x in division.values():
        for y in x.values():
            y.sort(key=lambda n: n['group_name'])
    for case_id in new_cases:
        try:
            # 过滤非指定类型
            if case_id[0] not in ['L', 'G']:
                continue
            case_insert_list.append(CaseCreateModel(case_id=case_id))
            # 先算分析，主辅分析求和，求余
            analysis_count_sum = sum([sum([y['quantities'] for y in x['division']]) for x in division[case_id[0]]['analysis']])
            analysis_cache = int(case_id[7:]) % analysis_count_sum
            if analysis_cache == 0:
                analysis_cache = analysis_count_sum
            for x in division[case_id[0]]['analysis']:
                # 编号大于该组分工总和，则计算下一组
                if analysis_cache - sum([y['quantities'] for y in x['division']]) > 0:
                    analysis_cache = analysis_cache - sum([y['quantities'] for y in x['division']])
                else:
                    # 第一个人主分析
                    if analysis_cache <= x['division'][0]['quantities']:
                        analysis_insert_list.append(
                            AnalysisCreateModel(case_id=case_id, user_id=x['division'][0]['user_id'],
                                                user_name=x['division'][0]['user_name'], is_main=True))
                        analysis_insert_list.append(
                            AnalysisCreateModel(case_id=case_id, user_id=x['division'][1]['user_id'],
                                                user_name=x['division'][1]['user_name'], is_main=False))
                        break
                    # 第二个人主分析
                    else:
                        analysis_insert_list.append(
                            AnalysisCreateModel(case_id=case_id, user_id=x['division'][1]['user_id'],
                                                user_name=x['division'][1]['user_name'], is_main=True))
                        analysis_insert_list.append(
                            AnalysisCreateModel(case_id=case_id, user_id=x['division'][0]['user_id'],
                                                user_name=x['division'][0]['user_name'], is_main=False))
                        break
            # 算计数
            count_cache = int(case_id[5:]) % sum(x['quantities'] for x in division[case_id[0]]['count'])
            for x in division[case_id[0]]['count']:
                if count_cache < x['quantities']:
                    count_insert_list.append(
                        CountCreateModel(case_id=case_id, user_id=x['user_id'], user_name=x['user_name']))
                    break
                else:
                    count_cache = count_cache - x['quantities']
        except Exception:
            traceback.print_exc()
            print(case_id)
    if case_insert_list:
        await create_case_with_analysis_and_count(conn=db, case_item=case_insert_list,
                                                  analysis_item=analysis_insert_list, count_item=count_insert_list)
