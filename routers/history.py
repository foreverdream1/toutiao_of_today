from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import history as history_crud
from crud.news import get_news_detail
from models.users import User
from schemas.history import (
    BrowseHistoryAddRequest,
    BrowseHistoryAddResponse,
    BrowseHistoryListResponse,
    BrowseHistoryNewsItemResponse,
)
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/history", tags=["浏览历史"])


@router.post("/add")
async def add_browse_history(
    data: BrowseHistoryAddRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    news = await get_news_detail(db, data.news_id)
    if news is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在",
        )
    record = await history_crud.upsert_browse_history(db, user.id, data.news_id)
    payload = BrowseHistoryAddResponse(
        id=record.id,
        user_id=record.user_id,
        news_id=record.news_id,
        view_time=record.viewed_at,
    )
    return success_response(message="添加成功", data=payload)


@router.get("/list")
async def get_browse_history_list(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, alias="page"),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
):
    rows, total = await history_crud.get_browse_history_list(
        db, user.id, page, page_size
    )
    history_list: list[BrowseHistoryNewsItemResponse] = []
    for news, view_time, history_id in rows:
        history_list.append(
            BrowseHistoryNewsItemResponse(
                id=news.id,
                title=news.title,
                description=news.description,
                image=news.image,
                author=news.author,
                categoryId=news.category_id,
                views=news.views,
                publishTime=news.publish_time,
                historyId=history_id,
                viewTime=view_time,
            )
        )
    has_more = total > page * page_size
    data = BrowseHistoryListResponse(
        list=history_list,
        total=total,
        hasMore=has_more,
    )
    return success_response(message="success", data=data)


@router.delete("/delete/{history_id}")
async def delete_browse_history(
    history_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await history_crud.delete_browse_history_by_id(
        db, user.id, history_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="浏览记录不存在",
        )
    return success_response(message="删除成功", data=None)


@router.delete("/clear")
async def clear_browse_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await history_crud.clear_all_browse_history(db, user.id)
    return success_response(message="清空成功", data=None)
