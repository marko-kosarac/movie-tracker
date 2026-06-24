from pydantic import BaseModel


class AddToListRequest(BaseModel):
    item_id: int
    item_type: str  
