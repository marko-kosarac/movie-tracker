from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.database import Base


class UserListItem(Base):
    __tablename__ = "user_list_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, nullable=False)
    item_type = Column(String, nullable=False)   
    list_type = Column(String, nullable=False)   

    __table_args__ = (
        UniqueConstraint("user_id", "item_id", "item_type", name="uq_user_item"),
    )
