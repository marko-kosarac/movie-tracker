from typing import List, Literal, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import decode_access_token
from app.ai.agent import handle_message

router = APIRouter(prefix="/ai", tags=["AI"])
_bearer = HTTPBearer(auto_error=False)


def _optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[int]:
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    return payload.get("user_id")


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


def get_last_user_message(messages: List[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return ""


@router.post("/chat")
def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_optional_user_id),
):
    user_message = get_last_user_message(request.messages)

    if not user_message:
        return {"category": "ERROR", "answer": "Nisam dobio korisničku poruku."}

    result = handle_message(
        db=db,
        user_message=user_message,
        conversation_messages=request.messages[-10:],
        user_id=user_id,
    )

    return {
        "category": result["category"],
        "answer": result["answer"],
    }


@router.post("/chat-stream")
def chat_with_ai_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_optional_user_id),
):
    from app.ai.agent import handle_message_stream

    user_message = get_last_user_message(request.messages)

    if not user_message:
        return StreamingResponse(
            iter(["Nisam dobio korisničku poruku."]),
            media_type="text/plain",
        )

    return StreamingResponse(
        handle_message_stream(
            db=db,
            user_message=user_message,
            conversation_messages=request.messages[-10:],
            user_id=user_id,
        ),
        media_type="text/plain",
    )


@router.post("/index")
def index_ai_database(db: Session = Depends(get_db)):
    from app.ai.vector_store import index_movies_and_shows

    index_movies_and_shows(db)

    return {"message": "MovieTracker AI vector database indexed successfully."}


@router.get("/stats")
def ai_stats():
    from app.ai.vector_store import get_collection_stats

    return get_collection_stats()


@router.get("/search-debug")
def search_debug(query: str):
    from app.ai.vector_store import semantic_search

    results = semantic_search(query=query, limit=20, min_rating=0)

    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "id": item["id"],
                "type": item["type"],
                "title": item["title"],
                "year": item["year"],
                "imdb_rating": item["imdb_rating"],
                "genre": item["genre"],
            }
            for item in results
        ],
    }


@router.get("/plan-debug")
def plan_debug(query: str, db: Session = Depends(get_db)):
    from app.ai.agent import create_plan, database_search, semantic_only_search, hybrid_search

    plan = create_plan(query)
    mode = plan.get("mode")

    if mode == "DATABASE_SEARCH":
        results = database_search(db, plan)
    elif mode == "SEMANTIC_SEARCH":
        results = semantic_only_search(plan, query)
    elif mode == "HYBRID_SEARCH":
        results = hybrid_search(db, plan, query)
    else:
        results = []

    return {
        "query": query,
        "plan": plan,
        "results": results,
    }