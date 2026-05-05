from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud.users import get_user_by_token
from models.users import User
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdateRequest, UserChangePasswordRequest
from crud import users
from utils.auth import get_current_user
from utils.response import success_response

router=APIRouter(prefix="/api/user",tags=["用户"])

@router.post('/register')
async def register(user_data:UserRequest,db:AsyncSession=Depends(get_db)):#用户信息，db
    #注册逻辑：验证用户是否存在-》创建用户-》生成token-》响应结果
    existing_user =await users.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="用户名已存在")
    user = await users.create_user(db, user_data)
    token = await users.create_token(db, user.id)
    # return {
    #     "code":200,
    #     "message":"注册成功",
    #     "data":{
    #         "token":token,
    #         "user_info":{
    #             "id":user.id,
    #             "username":user.username,
    #             "avatar":user.avatar,
    #             "bio": user.bio
    #         }
    #     }
    # }

    response_data=UserAuthResponse(token=token,userInfo=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功",data=response_data)


@router.post("/login")
async def login(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    # 1. 统一交给 authenticate_user 处理“查用户+验密码”的逻辑
    user = await users.authenticate_user(db, user_data.username, user_data.password)
    # 2. 如果返回 None，说明用户名不存在或密码错误
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    # 3. 验证通过，直接生成 Token 并返回 (删掉多余且报错的 check_password 判断)
    token = await users.create_token(db, user.id)
    # 4. 组装并返回成功响应
    response_data = UserAuthResponse(
        token=token,
        userInfo=UserInfoResponse.model_validate(user)
    )
    return success_response(message="登录成功", data=response_data)

#查token查用户-》封装crud-》功能整合成一个工具函数-》路由函数调用
@router.get("/info")
async def get_user_info(user:User=Depends(get_current_user)):
    #获取用户信息逻辑：验证用户是否存在-》获取用户信息-》响应结果
    
    return success_response(message="获取用户信息成功",data=UserInfoResponse.model_validate(user))

@router.put("/update")
async def update_user_info(user_data:UserUpdateRequest,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    #更新用户信息逻辑：验证用户是否存在-》更新用户信息-》响应结果

    user = await users.update_user(db, user.username, user_data)
    return success_response(message="更新用户信息成功",data=UserInfoResponse.model_validate(user))


@router.put("/password")
async def update_password(password_data:UserChangePasswordRequest,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    res_change_pwd = await users.change_password(db, user, password_data.old_password, password_data.new_password)
    if not res_change_pwd:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="修改密码失败")
    return success_response(message="修改密码成功",data=res_change_pwd)