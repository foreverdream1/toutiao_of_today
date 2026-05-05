from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import NewItemBase


class BrowseHistoryAddRequest(BaseModel):
    """添加浏览记录请求体"""

    news_id: int = Field(..., description="新闻ID", alias="newsId")

    model_config = ConfigDict(populate_by_name=True)


class BrowseHistoryAddResponse(BaseModel):
    """添加浏览记录响应 data"""

    id: int
    user_id: int = Field(..., alias="userId")
    news_id: int = Field(..., alias="newsId")
    view_time: datetime = Field(..., alias="viewTime")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class BrowseHistoryNewsItemResponse(NewItemBase):
    """浏览历史列表中单条新闻（含记录 ID 与浏览时间）"""

    history_id: int = Field(..., alias="historyId")
    view_time: datetime = Field(..., alias="viewTime")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class BrowseHistoryListResponse(BaseModel):
    """浏览历史分页列表"""

    list: list[BrowseHistoryNewsItemResponse]
    total: int
    has_more: bool = Field(..., alias="hasMore")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
