from sqlalchemy import Column, Integer, String, Float, Text
from app.database import Base
from sqlalchemy.orm import relationship


class TVShow(Base):
    __tablename__ = "tv_shows"

    id = Column(Integer, primary_key = True, index = True)
    title = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    imdb_rating = Column(Float, nullable=True)
    poster = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    actors = Column(String, nullable=True)
    backdrop = Column(String, nullable=True)

    seasons = relationship("Season", back_populates="tv_show", cascade="all, delete")