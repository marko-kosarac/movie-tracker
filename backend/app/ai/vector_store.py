import chromadb
from openai import OpenAI
from sqlalchemy.orm import Session

from app.models.movie import Movie
from app.models.tv_show import TVShow

client = OpenAI()

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="cinetrack_items")


def _create_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def _build_movie_document(movie: Movie) -> str:
    return (
        f"Movie title: {movie.title}\n"
        f"Type: Movie\n"
        f"Year: {movie.year}\n"
        f"Genres: {movie.genre or 'Unknown'}\n"
        f"IMDb rating: {movie.imdb_rating or 'Unknown'}\n"
        f"Actors: {movie.actors or 'Unknown'}\n"
        f"Plot: {movie.description or 'No description available'}"
    )


def _build_tv_show_document(show: TVShow) -> str:
    return (
        f"TV show title: {show.title}\n"
        f"Type: TV Show\n"
        f"Year: {show.year}\n"
        f"Genres: {show.genre or 'Unknown'}\n"
        f"IMDb rating: {show.imdb_rating or 'Unknown'}\n"
        f"Actors: {show.actors or 'Unknown'}\n"
        f"Plot: {show.description or 'No description available'}"
    )


def index_movies_and_shows(db: Session):
    movies = db.query(Movie).all()
    shows = db.query(TVShow).all()

    documents = []
    embeddings = []
    ids = []
    metadatas = []

    for movie in movies:
        doc = _build_movie_document(movie)
        documents.append(doc)
        embeddings.append(_create_embedding(doc))
        ids.append(f"movie_{movie.id}")
        metadatas.append({
            "id": movie.id,
            "type": "movie",
            "title": movie.title,
            "year": movie.year or 0,
            "imdb_rating": movie.imdb_rating or 0,
            "genre": movie.genre or "",
            "description": movie.description or "",
            "actors": movie.actors or "",
        })

    for show in shows:
        doc = _build_tv_show_document(show)
        documents.append(doc)
        embeddings.append(_create_embedding(doc))
        ids.append(f"tv_show_{show.id}")
        metadatas.append({
            "id": show.id,
            "type": "tv_show",
            "title": show.title,
            "year": show.year or 0,
            "imdb_rating": show.imdb_rating or 0,
            "genre": show.genre or "",
            "description": show.description or "",
            "actors": show.actors or "",
        })

    if documents:
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )


def semantic_search(query: str, limit: int = 20, min_rating: float = 6.0) -> list[dict]:
    query_embedding = _create_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
    )

    items = []

    for i in range(len(results["ids"][0])):
        metadata = results["metadatas"][0][i]
        rating = metadata.get("imdb_rating", 0) or 0

        if rating < min_rating:
            continue

        items.append({
            "id": metadata["id"],
            "type": metadata["type"],
            "title": metadata["title"],
            "year": metadata["year"],
            "imdb_rating": rating,
            "genre": metadata["genre"],
            "description": metadata.get("description", ""),  
            "actors": metadata.get("actors", ""),
            "document": results["documents"][0][i],         
        })

    return items


def get_collection_stats() -> dict:
    return {
        "count": collection.count()
    }