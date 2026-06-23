from pydantic import BaseModel, computed_field
from typing import List, Optional
from .season import SeasonOut


class TVShowBase(BaseModel):
    title: str
    year: Optional[int]
    imdb_rating: Optional[float]
    poster: Optional[str]
    backdrop: Optional[str]
    genre: Optional[str]
    description: Optional[str]
    actors: Optional[str]

class TVShowList(TVShowBase):
    id: int
    seasons: List[SeasonOut] = []

    @computed_field
    @property
    def seasons_count(self) -> int:
        return len(self.seasons)

    class Config:
        from_attributes = True

class TVShowCreate(TVShowBase):
    pass

class TVShowDetail(TVShowBase):
    id: int
    seasons: List[SeasonOut] = []

    class Config:
        from_attributes = True

class TVShowOut(TVShowBase):
    id: int
    seasons: List[SeasonOut] = []

    class Config:
        from_attributes = True