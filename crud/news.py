from sqlalchemy.ext.asyncio import AsyncSession
from models.news import Category, News
from sqlalchemy import select, func, update


async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 10):
    stmt = select(Category).offset(skip).limit(limit)
    stmt_result = await db.execute(stmt)
    categories = stmt_result.scalars().all()
    return categories


async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 10):
    # 查询的是指定分类下的新闻列表
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_news_count(db: AsyncSession, category_id: int):
    # 统计的是指定分类下的新闻列表
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one()  # 只能有一个结果，否则会报错


async def get_news_detail(db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def increase_news_views(db: AsyncSession, news_id: int):
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(stmt)
    await db.commit()
    # 更新-》检查数据库是否整的命中数据——》命中返回true，否则返回false
    return result.rowcount > 0


async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    # orderby-》排序
    stmt = select(News).where((News.category_id == category_id) & (News.id != news_id)).order_by(News.views.desc(),
                                                                                                 News.publish_time.desc()).limit(
        limit)
    result = await db.execute(stmt)
    related_news = result.scalars().all()
    # 列表推导式 推导出新闻的核心数据在return
    return [{
        "id": news_detail.id,
        "title": news_detail.title,
        "description": news_detail.description,
        "content": news_detail.content,
        "image": news_detail.image,
        "author": news_detail.author,
        "category_id": news_detail.category_id,
        "views": news_detail.views

    } for news_detail in related_news]
