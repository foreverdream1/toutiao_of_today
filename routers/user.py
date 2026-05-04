from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse
from crud import users
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
async def login(user_data:UserRequest,db:AsyncSession=Depends(get_db)):
    user = await users.authenticate_user(db, user_data.username,user_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="用户名或密码错误")
    if not user.check_password(user_data.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="密码错误")
    token = await users.create_token(db, user.id)
    response_data=UserAuthResponse(token=token,userInfo=UserInfoResponse.model_validate(user))
    return success_response(message="登录成功",data=response_data)