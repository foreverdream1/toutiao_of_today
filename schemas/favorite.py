from pydantic import BaseModel, Field


class FavoriteCheckResponse(BaseModel):
    is_favorite:bool=Field(...,description="isFavorite")


class FavoriteAddRequest(BaseModel):
    news_id:int=Field(...,description="新闻ID")
