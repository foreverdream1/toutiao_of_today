from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import news_cache  # 统一走带缓存的 CRUD 层

router = APIRouter(prefix="/api/news", tags=["新闻"])


# ──────────────────────────────────────────────────────
# GET /api/news/categories  获取新闻分类列表
# ──────────────────────────────────────────────────────
@router.get("/categories")
async def list_categories(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取新闻分类列表（Redis 缓存 TTL 2h）
    """
    skip = (page - 1) * limit
    categories = await news_cache.get_categories(db, skip, limit)

    # 兼容缓存返回 list[dict] 与 DB 返回 list[ORM] 两种类型
    def _to_dict(c):
        if isinstance(c, dict):
            return {"id": c["id"], "name": c["name"], "sort_order": c["sort_order"]}
        return {"id": c.id, "name": c.name, "sort_order": c.sort_order}

    return {
        "code": 200,
        "message": "获取新闻分类列表成功",
        "data": [_to_dict(c) for c in categories],
    }


# ──────────────────────────────────────────────────────
# GET /api/news/list  获取新闻分页列表
# ──────────────────────────────────────────────────────
@router.get("/list")
async def get_news_list(
    category_id: int = Query(..., alias="categoryId", description="新闻分类ID"),
    page: int = Query(1, ge=1, description="页码，最小为1"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量，1-100"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取分类下新闻分页列表（Redis 缓存 TTL 5min）
    返回值已包含 total，无需额外查询 DB。
    """
    result = await news_cache.get_news_list(db, category_id, page, page_size)

    # 兼容缓存返回 dict 与 DB 直接组装 dict 两种场景
    news_list = result.get("list", [])
    total = result.get("total", 0)
    offset = (page - 1) * page_size

    return {
        "code": 200,
        "message": "获取新闻列表成功",
        "data": {
            "list": news_list,
            "total": total,
            "hasMore": (offset + len(news_list)) < total,
        },
    }


# ──────────────────────────────────────────────────────
# GET /api/news/detail  获取新闻详情
# ──────────────────────────────────────────────────────
@router.get("/detail")
async def get_news_detail(
    news_id: int = Query(..., alias="newsId", description="新闻ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取新闻详情 + 浏览量自增（Redis 计数器，异步写回 DB）+ 相关新闻。
    新闻详情 Redis 缓存 TTL 10min；相关新闻 TTL 10min。
    """
    detail = await news_cache.get_news_detail(db, news_id)
    if not detail:
        raise HTTPException(status_code=404, detail="新闻不存在")

    # 浏览量自增（Redis 计数器，达阈值写回 DB）
    await news_cache.increase_news_views(db, news_id)

    # 获取相关新闻（需要 category_id）
    cat_id = detail.get("category_id") if isinstance(detail, dict) else detail.category_id
    related = await news_cache.get_related_news(db, news_id, cat_id)

    # 统一序列化输出
    def _field(obj, key):
        return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)

    return {
        "code": 200,
        "message": "获取新闻详情成功",
        "data": {
            "id": _field(detail, "id"),
            "title": _field(detail, "title"),
            "description": _field(detail, "description"),
            "content": _field(detail, "content"),
            "image": _field(detail, "image"),
            "author": _field(detail, "author"),
            "category_id": cat_id,
            "categoryId": cat_id,
            "views": _field(detail, "views"),
            "publish_time": str(_field(detail, "publish_time")),
            "relatedNews": related,
        },
    }
