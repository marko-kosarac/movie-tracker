from pydantic import BaseModel
from typing import List
from .episode import EpisodeOut


class SeasonBase(BaseModel):
    season_number: int


class SeasonCreate(SeasonBase):
    tv_show_id: int


class SeasonOut(SeasonBase):
    id: int
    episodes: List[EpisodeOut] = []

    class Config:
        from_attributes = True