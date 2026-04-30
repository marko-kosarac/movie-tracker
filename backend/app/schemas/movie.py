from pydantic import BaseModel
from typing import Optional


class MovieBase(BaseModel):
    title: str
    year: int
    imdb_rating: Optional[float] = None
    poster: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    actors: Optional[str] = None
    backdrop: Optional[str] = None


class MovieCreate(MovieBase):
    pass


class MovieResponse(MovieBase):
    id: int

    class Config:
        from_attributes = True