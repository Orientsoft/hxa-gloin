from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import HTTP_400_BAD_REQUEST
# custom defined
from app.models.user import UserCreate, User, TokenResponse, UserListResponse, UserCreateRequest, RolePatchRequest, \
    RoleCreateModel, GroupEnum, CaseTypeEnum, DivisionCreateModel, RoleWithDivisionModel
from app.crud.user import create_user, get_user, get_user_list_by_query_with_page_and_limit, count_user_by_query, \
    get_user_by_name, update_role_with_item, create_role_with_item, delete_group_by_query, \
    get_one_group_by_query, get_one_user_by_query, create_division_with_item, get_one_division_by_query, \
    update_division_by_query_with_item, get_group_list, get_division_list_unfold_user_by_query, delete_user_by_query, \
    delete_division_by_query, update_user_info_by_query_with_item
from app.dependencies.jwt import get_current_user_authorizer
from app.utils.jwt import create_access_token
from app.db.mongodb import AsyncIOMotorClient, get_database
from app.core.config import api_key as API_KEY
from app.utils.security import generate_salt, get_password_hash, verify_password

router = APIRouter()


@router.post("/users/login", response_model=TokenResponse, tags=["user"], name='账号密码登录')
async def login(user: OAuth2PasswordRequestForm = Depends(), db: AsyncIOMotorClient = Depends(get_database)):
    dbuser = await get_user(conn=db, query={'username': user.username})
    if not dbuser:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='用户名错误')
    elif not dbuser.check_password(user.password):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='密码错误')
    token = create_access_token(data={"id": dbuser.id})
    # swaggerui 要求返回此格式
    return TokenResponse(access_token=token)


@router.post('/user', tags=['admin'], name='单个用户添加')
async def post_users(
        username: str = Body(...), is_admin: bool = Body(...), password: str = Body(...), realname: str = Body(...),
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    if not user.is_admin:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='权限不足')
    data_user = await get_user(conn=db, query={'username': username})
    # 用户名重复
    if data_user:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='用户名重复')
    user_model = UserCreate(
        username=username,
        password=password,
        realname=realname,
        is_admin=is_admin
    )
    await create_user(conn=db, user=user_model)
    return {'data': {'id': user_model.id}}


@router.get('/user_list', tags=['admin'], response_model=UserListResponse, name='用户列表获取')
async def get_user_list(
        search: str = None, page: int = 1, limit: int = 20,
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    if not user.is_admin:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='权限不足')
    data_user = await get_user_list_by_query_with_page_and_limit(conn=db,
                                                                 query={'$or': [{'username': {'$regex': search}}, {
                                                                     'realname': {
                                                                         '$regex': search}}]} if search else {},
                                                                 page=page, limit=limit)
    total = await count_user_by_query(conn=db, query={'$or': [{'username': {'$regex': search}}, {
        'realname': {
            '$regex': search}}]} if search else {})
    return UserListResponse(data=data_user, total=total)


@router.get('/user/me', tags=['user'], name='用户个人信息')
async def user_me(
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    dbuser = await get_user(conn=db, query={'id': user.id})
    return {'username': dbuser.username, 'is_admin': dbuser.is_admin, 'realname': dbuser.realname, 'id': dbuser.id}


@router.post("/users/init", tags=["user"], name='初始化管理员')
async def add_admin(data: UserCreateRequest = Body(...), api_key: str = Body(...),
                    db: AsyncIOMotorClient = Depends(get_database)):
    if api_key != API_KEY:
        raise HTTPException(HTTP_400_BAD_REQUEST, 'apikey错误')
    db_user = await get_user_by_name(conn=db, name=data.username)
    if db_user:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Name already registered")
    await create_user(conn=db, user=UserCreate(**data.dict()))
    return {'msg': '初始化成功'}


@router.delete('/user', tags=['admin'], name='删除用户')
async def delete_user(
        user_id: str,
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    if not user.is_admin:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='权限不足')
    data_division = await get_one_division_by_query(conn=db, query={'user_id': user_id})
    if data_division:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='该用户还有任务，不可删除')
    await delete_user_by_query(conn=db, query={'id': user_id})
    return {'msg': '操作成功'}


@router.patch('/user', tags=['user'], name='用户修改信息')
async def patch_user(
        realname: str,
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    await update_user_info_by_query_with_item(conn=db, query={'id': user.id}, item={'$set': {'realname': realname}})
    return {'msg': '操作成功'}


@router.patch('/user/password', tags=['user'], name='用户修改密码')
async def patch_user_password(
        old_password: str, new_password: str,
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    data_user = await get_user(conn=db, query={'id': user.id})
    if not data_user.check_password(password=old_password):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='旧密码错误')
    item = {}
    salt = generate_salt()
    hashed_password = get_password_hash(salt + new_password)
    item['salt'] = salt
    item['hashed_password'] = hashed_password
    await update_user_info_by_query_with_item(conn=db, query={'id': user.id}, item={'$set': item})
    return {'msg': '操作成功'}


@router.patch('/group', tags=['admin'], name='修改角色分工')
async def patch_group(
        group_id: str = Body(...), group_name: str = Body(...),
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    if not user.is_admin:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='权限不足')
    await update_role_with_item(conn=db, query={'id': group_id}, item=RolePatchRequest(group_name=group_name))
    return {'msg': '修改成功'}


@router.post('/group', tags=['admin'], name='新增分组')
async def post_group(
        group_name: str = Body(...), group_type: GroupEnum = Body(...),
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    if not user.is_admin:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='权限不足')
    group_id = await create_role_with_item(conn=db, item=RoleCreateModel(group_type=group_type, group_name=group_name))
    return {'data': {'group_id': group_id}}


@router.get('/group', tags=['user', 'admin'], name='获取角色分组分工信息')
async def get_group(
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    data_group = await get_group_list(conn=db)
    return_obj = []
    for x in data_group:
        data_division = await get_division_list_unfold_user_by_query(conn=db, query={'group_id': x.id})
        return_obj.append(RoleWithDivisionModel(
            id=x.id,
            group_name=x.group_name,
            group_type=x.group_type,
            division=data_division
        ))
    return return_obj


@router.delete('/group', tags=['admin'], name='删除分组')
async def delete_group(
        group_id: str,
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    # TODO 需要校验并确定该分组下已没有分工
    if user.is_admin is False:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='权限不足')
    data_division = await get_one_division_by_query(conn=db, query={'group_id': group_id})
    if data_division:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='该分组下还有任务，不可删除')
    await delete_group_by_query(conn=db, query={'id': group_id})
    return {'msg': '操作成功'}


@router.post('/division', tags=['admin'], name='新增角色分工')
async def post_division(
        group_id: str = Body(...), user_id: str = Body(...), case_type: CaseTypeEnum = Body(...),
        quantities: int = Body(...),
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    if user.is_admin is False:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='权限不足')
    data_group = await get_one_group_by_query(conn=db, query={'id': group_id})
    if not data_group:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='无效的分组')
    data_user = await get_one_user_by_query(conn=db, query={'id': user_id})
    if not data_user:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='无效的用户')
    data_division = await get_one_division_by_query(conn=db, query={
        'group_id': group_id,
        'user_id': user_id,
        'case_type': case_type
    })
    if data_division:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='该用户已有相应分工，不可重复分配')
    division_id = await create_division_with_item(conn=db, item=DivisionCreateModel(
        group_id=group_id,
        user_id=user_id,
        case_type=case_type,
        quantities=quantities
    ))
    return {'data': {'division_id': division_id}}


@router.patch('/division', tags=['admin'], name='修改角色分工')
async def patch_division(
        division_id: str = Body(...), quantities: int = Body(...),
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    if user.is_admin is False:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='权限不足')
    data_division = await get_one_division_by_query(conn=db, query={'id': division_id})
    if not data_division:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='无效的分组')
    await update_division_by_query_with_item(conn=db, query={'id': division_id},
                                             item={'$set': {'quantities': quantities}})
    return {'msg': '修改成功'}


@router.delete('/division', tags=['admin'], name='删除角色分工')
async def delete_division(
        division_id: str,
        user: User = Depends(get_current_user_authorizer(required=True)),
        db: AsyncIOMotorClient = Depends(get_database)
):
    if user.is_admin is False:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='权限不足')
    await delete_division_by_query(conn=db, query={'id': division_id})
    return {'msg': '操作成功'}
