import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest, UserChangePasswordRequest
from utils import security
from utils.security import get_password_hash,verify_password


# 根据用户名查询数据库
async def get_user_by_username(db:AsyncSession,username:str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()

#创建用户
async def create_user(db:AsyncSession,user_data:UserRequest):
    #先密码加密-》add
    password_hash = security.get_password_hash(user_data.password)
    user = User(username=user_data.username, password=password_hash)
    db.add(user)
    await db.commit()
    await db.refresh(user)#从数据库刷新数据
    return user

#生成token
async def create_token(db:AsyncSession,user_id:int):
    #生成token->设置过期时间-》车讯数据库当前用户是否有token-》有则更新，没有则创建
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=7)
    stmt = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(stmt)
    user_token = result.scalar_one_or_none()
    if user_token:
        #更新
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        #创建
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
    await db.commit()
    return token

async def authenticate_user(db:AsyncSession,username:str,password:str):
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password):
        return None
    return user

#根据token车讯用户：验证token-》查询用户
async def get_user_by_token(db:AsyncSession,token:str):
    query = select(UserToken).where(UserToken.token == token)
    result = await  db.execute(query)
    db_token = result.scalar_one_or_none()
    if not db_token or db_token.expires_at<datetime.now():
        return None
    query1 = select(User).where(User.id == db_token.user_id)
    result1 =await db.execute(query1)
    return result1.scalar_one_or_none()

#更新用户信息
async def update_user(db:AsyncSession,username:str,user_data:UserUpdateRequest):
    query = update(User).where(User.username == username).values(
        **user_data.model_dump(exclude_unset=True, exclude_none=True))
    result = await db.execute(query)
    await db.commit()
    if result.rowcount==0:
        raise HTTPException(status_code=404,detail="用户不存在")

    #获取更新后的用户
    update_user = await get_user_by_username(db, username)
    return update_user

#修改密码：验证旧密码-》新密码加密-》修改密码
async def change_password(db:AsyncSession,user:User,old_password:str,new_password:str):
    if not security.verify_password(old_password, user.password):
        return False
    password_hash = security.get_password_hash(new_password)
    user.password=password_hash
    db.add(User)
    await db.commit()
    await db.refresh(user)
    return True