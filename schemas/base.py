from datetime import datetime
from typing import Optional

from pydantic import Field, BaseModel, ConfigDict


class NewItemBase(BaseModel):
    id:int
    title:str
    description:Optional[str]=None
    image:Optional[str]=None
    author:Optional[str]=None
    category_id:int=Field(alias="categoryId")
    views:int
    publish_time:Optional[datetime]=Field(None,alias="publishTime")

    model_config=ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )