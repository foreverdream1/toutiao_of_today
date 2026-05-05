from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from models.news import News
from models.users import User


class Base(DeclarativeBase):
    """SQLAlchemy 基础模型类"""

    pass


class BrowseHistory(Base):
    """
    浏览历史表 ORM 模型
    记录用户阅读新闻的行为；同一用户对同一新闻仅保留一条记录，再次浏览时更新浏览时间。
    """

    __tablename__ = "browse_history"

    __table_args__ = (
        UniqueConstraint("user_id", "news_id", name="uq_browse_history_user_news"),
        Index("idx_browse_history_user_id", "user_id"),
        Index("idx_browse_history_news_id", "news_id"),
        Index("idx_browse_history_user_viewed", "user_id", "viewed_at"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="浏览记录ID",
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(User.id),
        nullable=False,
        comment="用户ID",
    )
    news_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(News.id),
        nullable=False,
        comment="新闻ID",
    )
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="最近浏览时间",
    )

    def __repr__(self) -> str:
        return (
            f"<BrowseHistory(id={self.id}, user_id={self.user_id}, "
            f"news_id={self.news_id}, viewed_at={self.viewed_at})>"
        )
