import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User, UserToken
from schemas.users import UserRequest
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