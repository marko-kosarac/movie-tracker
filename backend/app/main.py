from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import Base, engine
from app.models.user import User
from app.models.user_list import UserListItem
from app.routes import auth, movies, tv_shows, ai
from app.routes import lists as lists_router
from app.models import Movie, TVShow, Season, Episode

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.ai.vector_store import collection
    count = collection.count()
    if count == 0:
        print("⚠️  ChromaDB is empty — semantic search will fall back to database search. Run indexing to enable semantic search.")
    else:
        print(f"✓ ChromaDB ready — {count} items indexed.")
    yield

app = FastAPI(title="CineTrack API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(tv_shows.router)
app.include_router(ai.router)
app.include_router(lists_router.router)

@app.get("/")
def root():
    return {"message": "CineTrack API is running"}