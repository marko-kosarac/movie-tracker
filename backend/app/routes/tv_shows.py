from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app.models.tv_show import TVShow
from app.models.season import Season
from app.models.episode import Episode

from app.schemas.tv_show import TVShowCreate, TVShowList, TVShowDetail
from app.schemas.season import SeasonOut
from app.schemas.episode import EpisodeOut
from app.schemas.season import SeasonCreate
from app.schemas.episode import EpisodeCreate


router = APIRouter(prefix="/tv-shows", tags=["TV Shows"])


@router.get("/", response_model=List[TVShowList])
def get_tv_shows(
    search: str | None = None,
    genre: str | None = None,
    sort: str = "rating",
    limit: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(TVShow).options(joinedload(TVShow.seasons))

    if search:
        query = query.filter(TVShow.title.ilike(f"%{search}%"))

    if genre and genre != "All":
        query = query.filter(TVShow.genre.ilike(f"%{genre}%"))

    if sort == "rating":
        query = query.order_by(TVShow.imdb_rating.desc())
    elif sort == "year_desc":
        query = query.order_by(TVShow.year.desc())
    elif sort == "year_asc":
        query = query.order_by(TVShow.year.asc())
    elif sort == "title_asc":
        query = query.order_by(TVShow.title.asc())
    elif sort == "title_desc":
        query = query.order_by(TVShow.title.desc())

    if limit:
        query = query.limit(limit)

    return query.all()


@router.get("/{tv_show_id}", response_model=TVShowDetail)
def get_tv_show(tv_show_id: int, db: Session = Depends(get_db)):
    tv_show = (
        db.query(TVShow)
        .options(joinedload(TVShow.seasons).joinedload(Season.episodes))
        .filter(TVShow.id == tv_show_id)
        .first()
    )

    if not tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")

    return tv_show


@router.post("/", response_model=TVShowList)
def create_tv_show(tv_show_data: TVShowCreate, db: Session = Depends(get_db)):
    tv_show = TVShow(**tv_show_data.model_dump())

    db.add(tv_show)
    db.commit()
    db.refresh(tv_show)

    return tv_show


@router.get("/{tv_show_id}/seasons", response_model=List[SeasonOut])
def get_tv_show_seasons(tv_show_id: int, db: Session = Depends(get_db)):
    tv_show = db.query(TVShow).filter(TVShow.id == tv_show_id).first()

    if not tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")

    return (
        db.query(Season)
        .filter(Season.tv_show_id == tv_show_id)
        .order_by(Season.season_number.asc())
        .all()
    )


@router.get("/seasons/{season_id}/episodes", response_model=List[EpisodeOut])
def get_season_episodes(season_id: int, db: Session = Depends(get_db)):
    season = db.query(Season).filter(Season.id == season_id).first()

    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    return (
        db.query(Episode)
        .filter(Episode.season_id == season_id)
        .order_by(Episode.episode_number.asc())
        .all()
    )

@router.post("/seasons", response_model=SeasonOut)
def create_season(season_data: SeasonCreate, db: Session = Depends(get_db)):
    tv_show = db.query(TVShow).filter(TVShow.id == season_data.tv_show_id).first()

    if not tv_show:
        raise HTTPException(status_code=404, detail="TV show not found")

    season = Season(**season_data.model_dump())

    db.add(season)
    db.commit()
    db.refresh(season)

    return season


@router.post("/episodes", response_model=EpisodeOut)
def create_episode(episode_data: EpisodeCreate, db: Session = Depends(get_db)):
    season = db.query(Season).filter(Season.id == episode_data.season_id).first()

    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    episode = Episode(**episode_data.model_dump())

    db.add(episode)
    db.commit()
    db.refresh(episode)

    return episode