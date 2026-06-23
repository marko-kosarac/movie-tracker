from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey("seasons.id"))
    episode_number = Column(Integer)

    title = Column(String)
    description = Column(String)

    season = relationship("Season", back_populates="episodes")