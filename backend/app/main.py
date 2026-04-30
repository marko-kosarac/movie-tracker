from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models.user import User
from app.routes import auth, movies
from app.models.movie import Movie

app = FastAPI(title="CineTrack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(movies.router)


@app.get("/")
def root():
    return {"message": "CineTrack API is running"}