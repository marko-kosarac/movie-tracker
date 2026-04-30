from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.movie import Movie
from app.schemas.movie import MovieCreate, MovieResponse


router = APIRouter(prefix="/movies", tags=["Movies"])


# @router.get("/", response_model=List[MovieResponse])
# def get_movies(db: Session = Depends(get_db)):
#     movies = db.query(Movie).all()
#     return movies


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    return movie


@router.get("/", response_model=List[MovieResponse])
def get_movies(
    search: str | None = None,
    genre: str | None = None,
    sort: str = "rating",
    limit: int | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Movie)

    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))

    if genre and genre != "All":
        query = query.filter(Movie.genre.ilike(f"%{genre}%"))

    if sort == "rating":
        query = query.order_by(Movie.imdb_rating.desc())
    elif sort == "year_desc":
        query = query.order_by(Movie.year.desc())
    elif sort == "year_asc":
        query = query.order_by(Movie.year.asc())
    elif sort == "title_asc":
        query = query.order_by(Movie.title.asc())
    elif sort == "title_desc":
        query = query.order_by(Movie.title.desc())

    if limit:
        query = query.limit(limit)

    return query.all()