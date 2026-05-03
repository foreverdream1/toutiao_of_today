from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CategoryBase(BaseModel):
    id: int
    name: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NewsBase(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    content: str
    image: Optional[str] = None
    author: Optional[str] = None
    category_id: int
    views: int
    publish_time: datetime

    class Config:
        from_attributes = True
