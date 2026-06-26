from sqlalchemy.orm import Session

from app.models.movie import Movie
from app.models.tv_show import TVShow


def search_movies_by_filters(
    db: Session,
    genre: str | None = None,
    min_rating: float | None = None,
    year: int | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    title: str | None = None,
    limit: int = 10,
):
    query = db.query(Movie)

    if title:
        query = query.filter(Movie.title.ilike(f"%{title}%"))

    if genre:
        query = query.filter(Movie.genre.ilike(f"%{genre}%"))

    if min_rating is not None:
        query = query.filter(Movie.imdb_rating >= min_rating)

    if year is not None:
        query = query.filter(Movie.year == year)

    if year_from is not None:
        query = query.filter(Movie.year >= year_from)

    if year_to is not None:
        query = query.filter(Movie.year <= year_to)

    movies = (
        query
        .order_by(Movie.imdb_rating.desc().nullslast())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": movie.id,
            "type": "movie",
            "title": movie.title,
            "year": movie.year,
            "imdb_rating": movie.imdb_rating,
            "genre": movie.genre,
            "description": movie.description,
            "actors": movie.actors,
        }
        for movie in movies
    ]


def search_tv_shows_by_filters(
    db: Session,
    genre: str | None = None,
    min_rating: float | None = None,
    year: int | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    title: str | None = None,
    limit: int = 10,
):
    query = db.query(TVShow)

    if title:
        query = query.filter(TVShow.title.ilike(f"%{title}%"))

    if genre:
        query = query.filter(TVShow.genre.ilike(f"%{genre}%"))

    if min_rating is not None:
        query = query.filter(TVShow.imdb_rating >= min_rating)

    if year is not None:
        query = query.filter(TVShow.year == year)

    if year_from is not None:
        query = query.filter(TVShow.year >= year_from)

    if year_to is not None:
        query = query.filter(TVShow.year <= year_to)

    shows = (
        query
        .order_by(TVShow.imdb_rating.desc().nullslast())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": show.id,
            "type": "tv_show",
            "title": show.title,
            "year": show.year,
            "imdb_rating": show.imdb_rating,
            "genre": show.genre,
            "description": show.description,
            "actors": show.actors,
        }
        for show in shows
    ]


def _get_movie_details(db: Session, movie_id: int):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()

    if not movie:
        return None

    return {
        "id": movie.id,
        "type": "movie",
        "title": movie.title,
        "year": movie.year,
        "imdb_rating": movie.imdb_rating,
        "genre": movie.genre,
        "description": movie.description,
        "actors": movie.actors,
        "poster": movie.poster,
        "backdrop": movie.backdrop,
    }


def _get_tv_show_details(db: Session, show_id: int):
    show = db.query(TVShow).filter(TVShow.id == show_id).first()

    if not show:
        return None

    return {
        "id": show.id,
        "type": "tv_show",
        "title": show.title,
        "year": show.year,
        "imdb_rating": show.imdb_rating,
        "genre": show.genre,
        "description": show.description,
        "actors": show.actors,
        "poster": show.poster,
        "backdrop": show.backdrop,
    }