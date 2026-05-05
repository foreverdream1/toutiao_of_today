from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from models.users import User
from schemas.favorite import FavoriteCheckResponse, FavoriteAddRequest
from utils.auth import get_current_user
from utils.response import success_response
from crud import  favorite

router=APIRouter(prefix="/api/favorite",tags=["收藏"])


@router.get("/check")
async def check_favorite(news_id:int=Query(...,description="新闻ID"),user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):

    is_favorite = await favorite.is_news_favorite(db, user.id, news_id)
    return success_response(message="检查收藏成功",data=FavoriteCheckResponse(is_favorite=is_favorite))

@router.post("/add")
async def add_favorite(data:FavoriteAddRequest,user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result = await favorite.add_news_favorite(db, user.id, data.news_id)
    return success_response(message="添加收藏成功",data=result )

@router.delete("/remove")
async def remove_favorite(news_id:int=Query(...,description="新闻ID"),user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    result = await favorite.remove_news_favorite(db, user_id=user.id, news_id=news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="收藏记录不存在")
    return success_response(message="删除收藏成功")