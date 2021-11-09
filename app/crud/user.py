from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from app.models.user import UserInDB, UserCreate, UserListModel, RolePatchRequest, RoleCreateModel, RoleModel, \
    DivisionCreateModel, DivisionModel, DivisionInRole, DivisionGroupByGroup
from app.utils.security import generate_salt, get_password_hash
from app.core.config import database_name, user_collection_name, group_collection_name, division_collection_name


async def get_user(conn: AsyncIOMotorClient, query: Optional[dict]) -> UserInDB:
    row = await conn[database_name][user_collection_name].find_one(query)
    return UserInDB(**row) if row else None


async def create_user(conn: AsyncIOMotorClient, user: UserCreate) -> UserInDB:
    salt = generate_salt()
    hashed_password = get_password_hash(salt + user.password)
    db_user = user.dict()
    db_user['salt'] = salt
    db_user['hashed_password'] = hashed_password
    del db_user['password']
    conn[database_name][user_collection_name].insert_one(db_user)
    return UserInDB(**user.dict())


async def get_user_list_by_query_with_page_and_limit(conn: AsyncIOMotorClient, query: Optional[dict], page: int,
                                                     limit: int):
    result = conn[database_name][user_collection_name].find(query).skip((page - 1) * limit).limit(limit)
    return [UserListModel(**x) async for x in result]


async def count_user_by_query(conn: AsyncIOMotorClient, query: Optional[dict]):
    result = await conn[database_name][user_collection_name].count_documents(query)
    return result


async def get_user_by_name(conn: AsyncIOMotorClient, name: str):
    result = await conn[database_name][user_collection_name].find_one({'username': name})
    return UserInDB(**result) if result else None


async def update_user_info_by_query_with_item(conn: AsyncIOMotorClient, query: dict, item: dict):
    conn[database_name][user_collection_name].update_one(query, item)
    return True


async def update_role_with_item(conn: AsyncIOMotorClient, query: dict, item: RolePatchRequest):
    conn[database_name][group_collection_name].update_one(query, {'$set': item.dict(exclude_none=True)})
    return True


async def create_role_with_item(conn: AsyncIOMotorClient, item: RoleCreateModel):
    conn[database_name][group_collection_name].insert_one(item.dict())
    return item.id


async def get_role_list(conn: AsyncIOMotorClient):
    result = conn[database_name][group_collection_name].aggregate([
        {'$lookup': {'from': division_collection_name, 'localField': 'id', 'foreignField': 'group_id',
                     'as': 'division'}},
        {'$lookup': {'from': user_collection_name, 'localField': 'division.user_id', 'foreignField': 'id',
                     'as': 'user'}},
        {'$unwind': {'path': '$division.user', 'preserveNullAndEmptyArrays': True}}
    ])
    return [x async for x in result]


async def get_group_list(conn: AsyncIOMotorClient):
    result = conn[database_name][group_collection_name].find()
    return [RoleModel(**x) async for x in result]


async def delete_group_by_query(conn: AsyncIOMotorClient, query: dict):
    conn[database_name][group_collection_name].delete_one(query)
    return True


async def get_one_group_by_query(conn: AsyncIOMotorClient, query: dict):
    result = await conn[database_name][group_collection_name].find_one(query)
    return RoleModel(**result) if result else None


async def get_one_user_by_query(conn: AsyncIOMotorClient, query: dict):
    result = await conn[database_name][user_collection_name].find_one(query)
    return result


async def create_division_with_item(conn: AsyncIOMotorClient, item: DivisionCreateModel):
    conn[database_name][division_collection_name].insert_one(item.dict())
    return item.id


async def get_one_division_by_query(conn: AsyncIOMotorClient, query: dict):
    result = await conn[database_name][division_collection_name].find_one(query)
    return DivisionModel(**result) if result else None


async def update_division_by_query_with_item(conn: AsyncIOMotorClient, query: dict, item: dict):
    conn[database_name][division_collection_name].update_one(query, item)
    return True


async def get_division_list_by_query(conn: AsyncIOMotorClient, query: dict):
    result = conn[database_name][division_collection_name].find(query)
    return [DivisionModel(**x) async for x in result]


async def get_division_list_unfold_user_by_query(conn: AsyncIOMotorClient, query: dict):
    result = conn[database_name][division_collection_name].aggregate([
        {'$match': query},
        {'$lookup': {'from': user_collection_name, 'localField': 'user_id', 'foreignField': 'id', 'as': 'user'}},
        {'$unwind': '$user'}
    ])
    return [DivisionInRole(
        id=x['id'],
        quantities=x['quantities'],
        user_id=x['user_id'],
        realname=x['user']['realname'],
        case_type=x['case_type']
    ) async for x in result]


async def delete_user_by_query(conn: AsyncIOMotorClient, query: dict):
    conn[database_name][user_collection_name].delete_one(query)
    return True


async def delete_division_by_query(conn: AsyncIOMotorClient, query: dict):
    conn[database_name][division_collection_name].delete_one(query)
    return True


async def get_all_division_group_by_group(conn: AsyncIOMotorClient):
    result = conn[database_name][division_collection_name].aggregate([
        {'$lookup': {'from': group_collection_name, 'localField': 'group_id', 'foreignField': 'id', 'as': 'group'}},
        {'$unwind': '$group'},
        {'$lookup': {'from': user_collection_name, 'localField': 'user_id', 'foreignField': 'id', 'as': 'user'}},
        {'$unwind': '$user'},
        {'$group': {
            '_id': {'group_id': '$group_id', 'group_name': '$group.group_name', 'group_type': '$group.group_type'},
            'division': {'$push': {'user_id': '$user_id', 'user_name': '$user.realname', 'quantities': '$quantities', 'case_type': '$case_type',
                                   'group_id': '$group_id', 'id': '$id'}}}},
    ])
    return [DivisionGroupByGroup(
        group_id=x['_id']['group_id'],
        group_name=x['_id']['group_name'],
        group_type=x['_id']['group_type'],
        division=[DivisionModel(
            id=y['id'],
            group_id=y['group_id'],
            user_id=y['user_id'],
            user_name=y['user_name'],
            quantities=y['quantities'],
            case_type=y['case_type']
        ) for y in x['division']]
    ) async for x in result]
