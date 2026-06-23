import os
import time
import requests
from dotenv import load_dotenv

from app.database import SessionLocal
from app.models.tv_show import TVShow
from app.models.season import Season
from app.models.episode import Episode

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"


def get_genres():
    url = f"{BASE_URL}/genre/tv/list"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    genres = response.json().get("genres", [])
    return {genre["id"]: genre["name"] for genre in genres}


def get_tv_show_details(tmdb_id):
    url = f"{BASE_URL}/tv/{tmdb_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()


def get_tv_show_actors(tmdb_id):
    url = f"{BASE_URL}/tv/{tmdb_id}/credits"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    cast = response.json().get("cast", [])
    actors = [actor["name"] for actor in cast[:5]]

    return ", ".join(actors)


def get_season_details(tmdb_id, season_number):
    url = f"{BASE_URL}/tv/{tmdb_id}/season/{season_number}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()


def import_tv_shows(pages=3, import_episodes=True):
    if not TMDB_API_KEY:
        print("TMDB_API_KEY is missing in .env")
        return

    db = SessionLocal()
    genre_map = get_genres()

    try:
        for page in range(1, pages + 1):
            url = f"{BASE_URL}/tv/popular"
            params = {
                "api_key": TMDB_API_KEY,
                "language": "en-US",
                "page": page,
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            shows = response.json().get("results", [])

            for item in shows:
                tmdb_id = item.get("id")
                title = item.get("name")
                first_air_date = item.get("first_air_date", "")
                year = int(first_air_date[:4]) if first_air_date else None

                poster_path = item.get("poster_path")
                backdrop_path = item.get("backdrop_path")

                if not tmdb_id or not title or not year or not poster_path or not backdrop_path:
                    continue

                details = get_tv_show_details(tmdb_id)
                actors = get_tv_show_actors(tmdb_id)

                genre_names = [
                    genre_map.get(genre_id)
                    for genre_id in item.get("genre_ids", [])
                    if genre_map.get(genre_id)
                ]

                tv_show_data = {
                    "title": title,
                    "year": year,
                    "imdb_rating": item.get("vote_average"),
                    "poster": f"{IMAGE_BASE_URL}{poster_path}",
                    "backdrop": f"{IMAGE_BASE_URL}{backdrop_path}",
                    "genre": ", ".join(genre_names),
                    "description": item.get("overview"),
                    "actors": actors,
                }

                existing_show = db.query(TVShow).filter(TVShow.title == title).first()

                if existing_show:
                    for key, value in tv_show_data.items():
                        setattr(existing_show, key, value)
                    tv_show = existing_show
                else:
                    tv_show = TVShow(**tv_show_data)
                    db.add(tv_show)
                    db.commit()
                    db.refresh(tv_show)

                if import_episodes:
                    seasons = details.get("seasons", [])

                    for season_item in seasons:
                        season_number = season_item.get("season_number")

                        if season_number is None or season_number == 0:
                            continue

                        existing_season = (
                            db.query(Season)
                            .filter(
                                Season.tv_show_id == tv_show.id,
                                Season.season_number == season_number,
                            )
                            .first()
                        )

                        if existing_season:
                            season = existing_season
                        else:
                            season = Season(
                                tv_show_id=tv_show.id,
                                season_number=season_number,
                            )
                            db.add(season)
                            db.commit()
                            db.refresh(season)

                        season_details = get_season_details(tmdb_id, season_number)
                        episodes = season_details.get("episodes", [])

                        for episode_item in episodes:
                            episode_number = episode_item.get("episode_number")
                            episode_title = episode_item.get("name")

                            if not episode_number or not episode_title:
                                continue

                            existing_episode = (
                                db.query(Episode)
                                .filter(
                                    Episode.season_id == season.id,
                                    Episode.episode_number == episode_number,
                                )
                                .first()
                            )

                            episode_data = {
                                "season_id": season.id,
                                "episode_number": episode_number,
                                "title": episode_title,
                                "description": episode_item.get("overview"),
                            }

                            if existing_episode:
                                for key, value in episode_data.items():
                                    setattr(existing_episode, key, value)
                            else:
                                db.add(Episode(**episode_data))

                        db.commit()
                        time.sleep(0.2)

                print(f"Imported/updated TV show: {title}")
                time.sleep(0.2)

            print(f"Page {page} imported successfully.")

    finally:
        db.close()

    print("TV shows import finished.")


if __name__ == "__main__":
    import_tv_shows(pages=3, import_episodes=True)