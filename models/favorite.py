from datetime import datetime
from sqlalchemy import UniqueConstraint, Index, Integer, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 导入关联的表模型
from models.users import User
from models.news import News


class Base(DeclarativeBase):
    """SQLAlchemy 基础模型类"""
    pass


class Favorite(Base):
    """
    收藏表 ORM 模型
    用户收藏新闻的中间关联表
    """
    __tablename__ = 'favorite'  # 表名（规范写法）

    # 联合唯一约束 + 索引配置
    __table_args__ = (
        # 一个用户只能收藏同一条新闻一次
        UniqueConstraint('user_id', 'news_id', name='user_news_unique'),
        # 索引：加速按用户ID查询收藏
        Index('fk_favorite_user_idx', 'user_id'),
        # 索引：加速按新闻ID查询收藏
        Index('fk_favorite_news_idx', 'news_id'),
    )

    # 字段定义
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="收藏ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(User.id),
        nullable=False,
        comment="用户ID"
    )
    news_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(News.id),
        nullable=False,
        comment="新闻ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="收藏时间"
    )

    def __repr__(self):
        return (
            f"<Favorite(id={self.id}, user_id={self.user_id}, "
            f"news_id={self.news_id}, created_at={self.created_at})>"
        )