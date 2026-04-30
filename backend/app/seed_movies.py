from app.database import SessionLocal
from app.models.movie import Movie
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

db = SessionLocal()

movies = [
    {
        "title": "The Shawshank Redemption",
        "year": 1994,
        "imdb_rating": 9.3,
        "poster": "https://m.media-amazon.com/images/I/71715eBi1sL._AC_SL1000_.jpg",
        "genre": "Drama",
        "description": "Two imprisoned men bond over a number of years, finding comfort and eventual redemption through acts of common decency.",
        "actors": "Tim Robbins, Morgan Freeman, Bob Gunton",
        "backdrop": "https://i.pinimg.com/1200x/9d/a8/7e/9da87ec39cddda6ccc3dcca7be02dfba.jpg"
    },
    {
        "title": "The Dark Knight",
        "year": 2008,
        "imdb_rating": 9.0,
        "poster": "https://cdn.shopify.com/s/files/1/1416/8662/products/dark_knight_english_original_film_art_spo_2000x.jpg?v=1562539378",
        "genre": "Action, Crime, Drama",
        "description": "Batman faces the Joker, a criminal mastermind who wants to create chaos in Gotham City.",
        "actors": "Christian Bale, Heath Ledger, Aaron Eckhart",
        "backdrop": "https://i.pinimg.com/736x/77/59/f3/7759f313447f46d8a7cd31b46201c93e.jpg"
    },
    {
        "title": "Inception",
        "year": 2010,
        "imdb_rating": 8.8,
        "poster": "https://image.tmdb.org/t/p/original/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",
        "genre": "Action, Adventure, Sci-Fi",
        "description": "A thief who steals corporate secrets through dream-sharing technology is given a chance to erase his criminal history.",
        "actors": "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page",
        "backdrop": "https://i.pinimg.com/1200x/f7/b7/75/f7b775e2a139bf66eeb000f225bb1ef3.jpg"
    }
]

for movie_data in movies:
    existing_movie = db.query(Movie).filter(Movie.title == movie_data["title"]).first()

    if existing_movie:
        for key, value in movie_data.items():
            setattr(existing_movie, key, value)
    else:
        movie = Movie(**movie_data)
        db.add(movie)

db.commit()
db.close()

print("Movies added/updated successfully.")