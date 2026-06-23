from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True)
    tv_show_id = Column(Integer, ForeignKey("tv_shows.id"))
    season_number = Column(Integer)

    tv_show = relationship("TVShow", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete")