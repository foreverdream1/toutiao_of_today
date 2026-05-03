from http.client import HTTPException

from fastapi import APIRouter, Depends, Query,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_conf import get_db
from crud import news
from crud.news import get_categories, get_news_list as crud_get_news_list, get_news_count,get_news_detail
from schemas.news import NewsBase

router = APIRouter(prefix="/api/news", tags=["新闻"])



@router.get("/categories")
async def list_categories(
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):

    skip = (page - 1) * limit  # 计算偏移量
    categories = await get_categories(db, skip, limit)
    data = [
        {"id": c.id, "name": c.name, "sort_order": c.sort_order}
        for c in categories
    ]
    return {
        "code": 200,
        "message": "获取新闻分类列表成功",
        "data": data
    }


@router.get("/list")
async def get_news_list(
    category_id: int = Query(..., alias="categoryId", description="新闻分类ID"),
    page: int = Query(1, ge=1, description="页码，最小为1"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量，1-100"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取新闻列表
    """
    # 思路：处理分页规则——》查询数据库——》返回数据
    offset = (page - 1) * page_size
    news_list = await crud_get_news_list(db, category_id, offset, page_size)
    total = await get_news_count(db, category_id)
    data_list = [NewsBase.model_validate(n).model_dump() for n in news_list]
    return {
        "code": 200,
        "message": "获取新闻列表成功",
        "data": {
            "list": data_list,
            "total": total,
            "hasMore": (offset + len(data_list)) < total
        }
    }

@router.get("/detail")
async def get_news_detail(
    news_id:int=Query(...,alias="newsId",description="新闻ID"),
    db:AsyncSession=Depends(get_db)
):
    """
    获取新闻详情+浏览量+1+相关新闻
    """
    news_detail = await news.get_news_detail(db, news_id)
    if not news_detail:
        raise HTTPException(status_code=404,detail="新闻不存在")

    views_result = await news.increase_news_views(db, news_detail.id)
    if not views_result:
        raise HTTPException(status_code=404,detail="新闻不存在")

    related_news = await news.get_related_news(db, news_id, news_detail.category_id)

    return {
        "code":200,
        "message":"获取新闻详情成功",
        "data":{
            "id":news_detail.id,
            "title":news_detail.title,
            "description":news_detail.description,
            "content":news_detail.content,
            "image":news_detail.image,
            "author":news_detail.author,
            "category_id":  news_detail.category_id,
            "views":news_detail.views,
            "publish_time":news_detail.publish_time,
            "categoryId":news_detail.category_id,
            "relatedNews":related_news
        }
    }
