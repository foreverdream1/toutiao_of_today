from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.browse_history import BrowseHistory
from models.news import News


async def upsert_browse_history(
    db: AsyncSession, user_id: int, news_id: int
) -> BrowseHistory:
    """
    添加或更新浏览记录：同一用户同一新闻只保留一条，再次浏览时刷新 viewed_at。
    """
    stmt = select(BrowseHistory).where(
        BrowseHistory.user_id == user_id,
        BrowseHistory.news_id == news_id,
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    now = datetime.utcnow()
    if record is not None:
        record.viewed_at = now
    else:
        record = BrowseHistory(user_id=user_id, news_id=news_id, viewed_at=now)
        db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_browse_history_list(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10
):
    """分页查询当前用户的浏览历史（按最近浏览时间倒序）。"""
    count_stmt = select(func.count(BrowseHistory.id)).where(
        BrowseHistory.user_id == user_id
    )
    total = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    query = (
        select(
            News,
            BrowseHistory.viewed_at.label("view_time"),
            BrowseHistory.id.label("history_id"),
        )
        .join(BrowseHistory, BrowseHistory.news_id == News.id)
        .where(BrowseHistory.user_id == user_id)
        .order_by(BrowseHistory.viewed_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = (await db.execute(query)).all()
    return rows, total


async def delete_browse_history_by_id(
    db: AsyncSession, user_id: int, history_id: int
) -> bool:
    """删除指定 ID 的浏览记录（仅当前用户）。"""
    stmt = delete(BrowseHistory).where(
        BrowseHistory.id == history_id,
        BrowseHistory.user_id == user_id,
    )
    result = await db.execute(stmt)
    await db.commit()
    return (result.rowcount or 0) > 0


async def clear_all_browse_history(db: AsyncSession, user_id: int) -> int:
    """清空当前用户全部浏览历史。"""
    stmt = delete(BrowseHistory).where(BrowseHistory.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return int(result.rowcount or 0)
