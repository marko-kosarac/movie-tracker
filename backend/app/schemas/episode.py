from pydantic import BaseModel
from typing import Optional


class EpisodeBase(BaseModel):
    episode_number: int
    title: str
    description: Optional[str]


class EpisodeCreate(EpisodeBase):
    season_id: int


class EpisodeOut(EpisodeBase):
    id: int

    class Config:
        from_attributes = True