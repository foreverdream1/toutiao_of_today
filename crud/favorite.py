from select import select
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News


async def is_news_favorite(db: AsyncSession, user_id: int, news_id: int):
    query = select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(query)
    # 是否有收藏记录

    return result.scalar_one_or_none() is not None


async def add_news_favorite(db: AsyncSession, user_id: int, news_id: int):
    favorite = Favorite(user_id=user_id, news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite


async def remove_news_favorite(db: AsyncSession, user_id: int, news_id: int):
    stmt = delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def get_favorite_list(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10):
    # 总量+收藏的新闻列表
    count = select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
    count_res = await db.execute(count)
    total = count_res.scalar_one()

    # 获取收藏列表- 连表查询 join（）+收藏时间分页 limit（）+offset（）
    offset = (page - 1) * page_size
    query = (select(News, Favorite.created_at.label("favorite_time"), Favorite.id.label("favorite_id")).join(Favorite,
                                                                                                             Favorite.news_id == News.id).where(
        Favorite.user_id == user_id).order_by(Favorite.created_at.desc()).offset(offset).limit(page_size))
    result = await db.execute(query)
    rows = result.all()
    return rows,total

async def remove_all_favorite(db:AsyncSession,user_id:int):
    stmt = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0