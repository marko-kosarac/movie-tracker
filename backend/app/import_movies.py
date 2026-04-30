import os
import requests
from dotenv import load_dotenv

from app.database import SessionLocal
from app.models.movie import Movie

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"


def get_genres():
    url = f"{BASE_URL}/genre/movie/list"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    genres = response.json()["genres"]
    return {genre["id"]: genre["name"] for genre in genres}


def get_movie_actors(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/credits"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    cast = response.json().get("cast", [])
    main_actors = [actor["name"] for actor in cast[:5]]

    return ", ".join(main_actors)

def import_movies_by_year(year, pages=5):
    db = SessionLocal()
    genre_map = get_genres()

    try:
        for page in range(1, pages + 1):
            url = f"{BASE_URL}/discover/movie"
            params = {
                "api_key": TMDB_API_KEY,
                "language": "en-US",
                "primary_release_year": year,
                "page": page,
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            movies = response.json().get("results", [])

            for item in movies:
                title = item.get("title")
                release_date = item.get("release_date", "")
                year = int(release_date[:4]) if release_date else None

                poster_path = item.get("poster_path")
                backdrop_path = item.get("backdrop_path")

                if not title or not year or not poster_path or not backdrop_path:
                    continue

                existing_movie = db.query(Movie).filter(Movie.title == title).first()

                genre_names = [
                    genre_map.get(g)
                    for g in item.get("genre_ids", [])
                    if genre_map.get(g)
                ]

                movie_data = {
                    "title": title,
                    "year": year,
                    "imdb_rating": item.get("vote_average"),
                    "poster": f"{IMAGE_BASE_URL}{poster_path}",
                    "backdrop": f"{IMAGE_BASE_URL}{backdrop_path}",
                    "genre": ", ".join(genre_names),
                    "description": item.get("overview"),
                    "actors": get_movie_actors(item["id"]),
                }

                if existing_movie:
                    for key, value in movie_data.items():
                        setattr(existing_movie, key, value)
                else:
                    db.add(Movie(**movie_data))

            db.commit()
            print(f"{year} page {page} done")

    finally:
        db.close()

if __name__ == "__main__":
    for year in range(2018, 2024):
        import_movies_by_year(year, pages=3)