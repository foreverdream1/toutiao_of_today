# crud/news_cache.py
# 新闻业务数据访问层（带 Redis 缓存版）
#
# 缓存策略说明：
#   - 新闻分类列表：TTL 2h，低频变更，命中率高
#   - 新闻分页列表：TTL 5min，中频更新，兼顾实时性与性能
#   - 新闻详情：   TTL 10min，读多写少，减少 DB 压力
#   - 相关新闻：   TTL 10min，每次详情页请求顺带查询
#   - 浏览量：     Redis 计数器原子自增（异步写回策略），
#                  避免每次请求都产生 MySQL UPDATE，显著降低写压力

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from cache.news_cache import (
    get_cached_category, set_cached_category,
    get_cached_news_list, set_cached_news_list,
    get_cached_news_detail, set_cached_news_detail,
    get_cached_related_news, set_cached_related_news,
    incr_cached_views, get_cached_views,
)
from models.news import Category, News


# ──────────────────────────────────────────────────────
# 新闻分类列表（带缓存）
# ──────────────────────────────────────────────────────

async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 10):
    """
    先查 Redis，命中直接返回；未命中则查 DB，并将结果写入缓存。
    注意：返回值可能是 list[dict]（来自缓存）或 list[Category]（来自 DB）。
    路由层统一用字段名访问即可，不影响业务逻辑。
    """
    cached = await get_cached_category()
    if cached:
        return cached

    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()

    if categories:
        # jsonable_encoder 把 ORM 对象转成可序列化的 dict/list
        await set_cached_category(jsonable_encoder(categories))

    return categories


# ──────────────────────────────────────────────────────
# 新闻分页列表（带缓存）
# ──────────────────────────────────────────────────────

async def get_news_list(
    db: AsyncSession,
    category_id: int,
    page: int = 1,
    page_size: int = 10,
):
    """
    带缓存的新闻分页列表查询。
    缓存 key 包含 category_id + page + page_size，保证每页独立缓存。
    返回 {"list": [...], "total": int}。
    """
    cached = await get_cached_news_list(category_id, page, page_size)
    if cached:
        return cached

    skip = (page - 1) * page_size

    # 并发查询列表与总数
    list_stmt = (
        select(News)
        .where(News.category_id == category_id)
        .order_by(News.publish_time.desc())
        .offset(skip)
        .limit(page_size)
    )
    count_stmt = select(func.count(News.id)).where(News.category_id == category_id)

    news_result = await db.execute(list_stmt)
    count_result = await db.execute(count_stmt)

    news_list = news_result.scalars().all()
    total = count_result.scalar_one()

    data = {
        "list": jsonable_encoder(news_list),
        "total": total,
    }
    await set_cached_news_list(category_id, page, page_size, data)
    return data


async def get_news_count(db: AsyncSession, category_id: int) -> int:
    """统计分类下新闻总数（供兼容旧接口使用，新接口直接用 get_news_list 返回的 total）"""
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one()


# ──────────────────────────────────────────────────────
# 新闻详情（带缓存）
# ──────────────────────────────────────────────────────

async def get_news_detail(db: AsyncSession, news_id: int):
    """
    带缓存的新闻详情查询。
    命中缓存时返回 dict，未命中时从 DB 查询并写缓存后返回 News ORM 对象。
    路由层需兼容两种返回类型（通过 dict.get 或 getattr 访问字段）。
    """
    cached = await get_cached_news_detail(news_id)
    if cached:
        return cached

    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news = result.scalar_one_or_none()

    if news:
        await set_cached_news_detail(news_id, jsonable_encoder(news))

    return news


# ──────────────────────────────────────────────────────
# 浏览量自增（Redis 计数器 + 异步写回策略）
# ──────────────────────────────────────────────────────

# 浏览量写回阈值：Redis 计数累积到此值时触发一次批量写回 DB
_VIEWS_FLUSH_THRESHOLD = 10


async def increase_news_views(db: AsyncSession, news_id: int) -> bool:
    """
    浏览量 +1 策略：
    1. Redis 计数器原子自增
    2. 当计数器达到阈值时，将累计增量一次性写回 MySQL，并重置计数器
    这样可以将 N 次 MySQL UPDATE 合并为 1 次，大幅降低 DB 写压力。
    """
    count = await incr_cached_views(news_id)
    if count is None:
        # Redis 不可用时降级直接写 DB
        return await _flush_views_to_db(db, news_id, 1)

    # 达到阈值，批量写回 DB
    if count >= _VIEWS_FLUSH_THRESHOLD:
        success = await _flush_views_to_db(db, news_id, count)
        if success:
            from cache.news_cache import reset_cached_views
            await reset_cached_views(news_id)
        return success

    return True


async def _flush_views_to_db(db: AsyncSession, news_id: int, increment: int) -> bool:
    """将浏览量增量写回 MySQL"""
    stmt = (
        update(News)
        .where(News.id == news_id)
        .values(views=News.views + increment)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


# ──────────────────────────────────────────────────────
# 相关新闻（带缓存）
# ──────────────────────────────────────────────────────

async def get_related_news(
    db: AsyncSession,
    news_id: int,
    category_id: int,
    limit: int = 5,
):
    """
    带缓存的相关新闻查询（同分类、按浏览量+发布时间倒序、排除自身）。
    """
    cached = await get_cached_related_news(news_id)
    if cached is not None:
        return cached

    stmt = (
        select(News)
        .where(
            (News.category_id == category_id) & (News.id != news_id)
        )
        .order_by(News.views.desc(), News.publish_time.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    related = result.scalars().all()

    data = [
        {
            "id": n.id,
            "title": n.title,
            "description": n.description,
            "image": n.image,
            "author": n.author,
            "category_id": n.category_id,
            "views": n.views,
            "publish_time": str(n.publish_time),
        }
        for n in related
    ]
    await set_cached_related_news(news_id, data)
    return data
