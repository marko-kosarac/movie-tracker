from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import decode_access_token
from app.models.user_list import UserListItem
from app.models.movie import Movie
from app.models.tv_show import TVShow
from app.schemas.user_list import AddToListRequest

router = APIRouter(prefix="/lists", tags=["Lists"])
security = HTTPBearer()


def get_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id


def _fetch_full_item(db: Session, item_id: int, item_type: str) -> dict | None:
    if item_type == "movie":
        obj = db.query(Movie).filter(Movie.id == item_id).first()
        if obj:
            return {
                "id": obj.id, "type": "movie", "title": obj.title,
                "year": obj.year, "imdb_rating": obj.imdb_rating,
                "poster": obj.poster, "genre": obj.genre,
                "description": obj.description, "actors": obj.actors,
                "backdrop": obj.backdrop,
            }
    elif item_type == "tv_show":
        obj = db.query(TVShow).filter(TVShow.id == item_id).first()
        if obj:
            return {
                "id": obj.id, "type": "tv_show", "title": obj.title,
                "year": obj.year, "imdb_rating": obj.imdb_rating,
                "poster": obj.poster, "genre": obj.genre,
                "description": obj.description, "actors": obj.actors,
                "backdrop": obj.backdrop,
            }
    return None


@router.get("/")
def get_lists(
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    rows = db.query(UserListItem).filter(UserListItem.user_id == user_id).all()

    watchlist, watched = [], []

    for row in rows:
        item = _fetch_full_item(db, row.item_id, row.item_type)
        if item:
            (watchlist if row.list_type == "watchlist" else watched).append(item)

    return {"watchlist": watchlist, "watched": watched}


@router.post("/watchlist", status_code=200)
def add_to_watchlist(
    data: AddToListRequest,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    existing = db.query(UserListItem).filter(
        UserListItem.user_id == user_id,
        UserListItem.item_id == data.item_id,
        UserListItem.item_type == data.item_type,
    ).first()

    if existing:
        if existing.list_type == "watched":
            raise HTTPException(status_code=400, detail="Item is already in watched list")
        return {"message": "Already in watchlist"}

    db.add(UserListItem(
        user_id=user_id,
        item_id=data.item_id,
        item_type=data.item_type,
        list_type="watchlist",
    ))
    db.commit()
    return {"message": "Added to watchlist"}


@router.post("/watched", status_code=200)
def add_to_watched(
    data: AddToListRequest,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    existing = db.query(UserListItem).filter(
        UserListItem.user_id == user_id,
        UserListItem.item_id == data.item_id,
        UserListItem.item_type == data.item_type,
    ).first()

    if existing:
        if existing.list_type == "watched":
            return {"message": "Already in watched"}
        existing.list_type = "watched"
        db.commit()
        return {"message": "Moved to watched"}

    db.add(UserListItem(
        user_id=user_id,
        item_id=data.item_id,
        item_type=data.item_type,
        list_type="watched",
    ))
    db.commit()
    return {"message": "Added to watched"}


@router.delete("/watchlist/{item_type}/{item_id}", status_code=200)
def remove_from_watchlist(
    item_type: str,
    item_id: int,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    entry = db.query(UserListItem).filter(
        UserListItem.user_id == user_id,
        UserListItem.item_id == item_id,
        UserListItem.item_type == item_type,
        UserListItem.list_type == "watchlist",
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Not found in watchlist")

    db.delete(entry)
    db.commit()
    return {"message": "Removed from watchlist"}


@router.delete("/watched/{item_type}/{item_id}", status_code=200)
def remove_from_watched(
    item_type: str,
    item_id: int,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    entry = db.query(UserListItem).filter(
        UserListItem.user_id == user_id,
        UserListItem.item_id == item_id,
        UserListItem.item_type == item_type,
        UserListItem.list_type == "watched",
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Not found in watched list")

    db.delete(entry)
    db.commit()
    return {"message": "Removed from watched"}
