from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, func, String, Index, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import Integer


class Base(DeclarativeBase):
    created_at:Mapped[datetime]=mapped_column(DateTime,insert_default=func.now(),default=func.now(),comment="创建时间")
    updated_at:Mapped[datetime]=mapped_column(DateTime,insert_default=func.now(),default=func.now(),onupdate=func.now(),comment="修改时间")


class Category(Base):
    __tablename__ = "news_category"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True,comment="分类id")
    name:Mapped[str]=mapped_column(String(50),unique=True,nullable=False,comment="分类名称")
    sort_order:Mapped[int]=mapped_column(Integer,default=0,nullable=False,comment="排序序号")

    def __repr__(self):
        return f"<Category(id={self.id},name={self.name},sort_order={self.sort_order})>"#打印对象相当于tostring


class News(Base):
    __tablename__ = "news"

    #创建索引：提升查询速度
    __table_args__ = (
        Index("idx_publish_time","publish_time"),#高并发查询
        Index('fk_news_category_idx','category_id')#按发布时间排序
    )
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True,comment="新闻id")
    title:Mapped[str]=mapped_column(String(255),nullable=False,comment="新闻标题")
    description:Mapped[Optional[str]]=mapped_column(String(500),nullable=False,comment="新闻描述")
    content:Mapped[str]=mapped_column(Text,nullable=False,comment="新闻内容")
    image:Mapped[Optional[str]]=mapped_column(String(255),nullable=False,comment="新闻图片")
    author:Mapped[Optional[str]]=mapped_column(String(100),nullable=False,comment="新闻作者")
    category_id:Mapped[int]=mapped_column(Integer,ForeignKey("news_category.id"),nullable=False,comment="新闻分类id")
    views:Mapped[int]=mapped_column(Integer,default=0,nullable=False,comment="新闻浏览量")
    publish_time:Mapped[datetime]=mapped_column(DateTime,default=func.now(),nullable=False,comment="新闻发布时间")

    def __repr__(self):
        return f"<News(id={self.id},title={self.title},description={self.description},content={self.content},image={self.image},author={self.author},category_id={self.category_id},views={self.views},publish_time={self.publish_time})>"