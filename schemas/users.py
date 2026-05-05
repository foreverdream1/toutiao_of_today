from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class UserRequest(BaseModel):
    username: str
    password: str

#user_info数据类型:基础类+info类（id，用户名）
class UserInfoBase(BaseModel):
    """
    用户信息响应模型
    """
    nickname:Optional[str]=Field(None,max_length=50,description="昵称")
    avatar:Optional[str]=Field(None,max_length=255,description="头像")
    bio:Optional[str]=Field(None,max_length=255,description="简介")
    gender:Optional[str]=Field(None,max_length=10,description="性别")


class UserInfoResponse(UserInfoBase):
    id:int
    username:str
    # 模型类配置
    model_config = ConfigDict(
        populate_by_name=True,  # alias/字段名兼容
        from_attributes=True,  # 允许从orm对象属性中取值
    )


#data数据类型
class UserAuthResponse(BaseModel):
    token:str
    user_info:UserInfoResponse=Field(...,alias="userInfo")

    #模型类配置
    model_config = ConfigDict(
        populate_by_name=True,#alias/字段名兼容
        from_attributes=True,#允许从orm对象属性中取值
    )


#更新用户信息的模型类
class UserUpdateRequest(BaseModel):
    nickname:str=None
    avatar:str=None
    gender:str=None
    bio:str=None
    phone:str=None

class UserChangePasswordRequest(BaseModel):
    old_password:str=Field(...,description="旧密码",alias="oldPassword")
    new_password:str=Field(...,description="新密码",min_length=6,alias="newPassword")