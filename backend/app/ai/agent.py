import json
from openai import OpenAI
from sqlalchemy.orm import Session

from app.ai.vector_store import semantic_search
from app.ai.tools import search_movies_by_filters, search_tv_shows_by_filters

client = OpenAI()


def build_conversation_context(conversation_messages=None) -> str:
    if not conversation_messages:
        return ""

    lines = []
    for msg in conversation_messages[-10:]:
        role = getattr(msg, "role", None) or msg.get("role")
        content = getattr(msg, "content", None) or msg.get("content")
        if role and content:
            lines.append(f"{role}: {content}")

    return "\n".join(lines)


PLANNER_PROMPT = """
You are the planning brain of MovieTracker AI.

Analyze the latest user message together with the conversation context and return a JSON plan.

The assistant can:
1. Answer directly for general movie/TV knowledge (NOT for recommending titles).
2. Answer follow-up questions about PREVIOUS results already shown in conversation context.
3. Use semantic vector search for vague recommendations, mood, similarity, atmosphere.
4. Use SQL/database filters for exact constraints like genre, year, rating, type.
5. Use hybrid search when the user combines vague meaning with exact filters.
6. Use action tools when the user wants to modify watchlist or watched list.

Return ONLY valid JSON.

Schema:
{
  "mode": "DIRECT_ANSWER" | "SEMANTIC_SEARCH" | "DATABASE_SEARCH" | "HYBRID_SEARCH" | "ACTION",
  "content_type": "movie" | "tv_show" | "both" | null,
  "semantic_query": string | null,
  "genre": string | null,
  "year": integer | null,
  "min_rating": number | null,
  "limit": integer,
  "action": string | null
}

Rules:
- Use DIRECT_ANSWER ONLY for: factual questions about cinema history, definitions, how the app works, or follow-up questions about titles already listed in the conversation context.
- NEVER use DIRECT_ANSWER when the user wants a list of movie/TV recommendations — that ALWAYS requires a database or semantic search.
- Use SEMANTIC_SEARCH for mood, vibe, similarity, vague recommendations, subgenre descriptions like "psychological thriller", "mind-bending", "dark", "mračno", "napeto".
- Use DATABASE_SEARCH for exact filter questions (specific genre, year, minimum rating).
- Use HYBRID_SEARCH when the request has both semantic meaning AND exact filters (e.g. "psychological thriller from 2010 with rating above 8").
- Use ACTION only when user clearly asks to change something (add to watchlist, mark as watched).
- If user says "best", "top", or "good", set min_rating to 7.0 unless they specify otherwise.
- If user does not specify limit, use 5.
- Always preserve exact year if user mentions it.
- For follow-up questions like "tell me more about the second one", "koji od njih", "drugi", "prethodni" — use DIRECT_ANSWER only if those titles are visible in conversation context.
"""


def create_plan(user_message: str, conversation_messages=None) -> dict:
    conversation_context = build_conversation_context(conversation_messages)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": PLANNER_PROMPT},
            {
                "role": "user",
                "content": f"""
                Conversation context:
                {conversation_context}

                Latest user message:
                {user_message}
                """,
            },
        ],
    )

    raw_plan = response.choices[0].message.content.strip()

    try:
        return json.loads(raw_plan)
    except json.JSONDecodeError:
        return {
            "mode": "DIRECT_ANSWER",
            "content_type": None,
            "semantic_query": None,
            "genre": None,
            "year": None,
            "min_rating": None,
            "limit": 5,
            "action": None,
        }


# ─── System prompts ───────────────────────────────────────────────────────────

DIRECT_SYSTEM_PROMPT = """
You are MovieTracker AI assistant. Always answer in Serbian.

You specialize in movies, TV shows, recommendations, and the MovieTracker app.

You may answer questions about the current conversation and follow-up questions
about titles already mentioned by the assistant in the conversation context.

If the user asks something completely unrelated to movies, TV shows, or MovieTracker,
politely redirect them back to those topics.

IMPORTANT: Do NOT invent or suggest movie/TV titles that were not shown to you.
If the user asks for recommendations, tell them you need to search the database first.
"""

CONTEXT_SYSTEM_PROMPT = """
You are MovieTracker AI assistant. Always answer in Serbian.

Your job is to recommend movies and TV shows STRICTLY from the provided MovieTracker database context.

Rules:
- NEVER mention or recommend any movie or TV show that is NOT listed in the database context below.
- Do not invent titles, directors, actors, or plot details.
- Do not say "you might also like X" if X is not in the context.
- If the context has fewer results than ideal, recommend only what is available and say so honestly.
- Choose the best 3 to 5 results from the context.
- Prefer higher IMDb rating when multiple results fit the request.
- Explain briefly why each result fits the user's request, using the provided descriptions.
- You may use conversation context to understand what the user is referring to (follow-up questions).
"""


def format_context(items: list[dict]) -> str:
    if not items:
        return "Nema rezultata."

    return "\n\n".join(
        f"Title: {item.get('title')}\n"
        f"Type: {item.get('type')}\n"
        f"Year: {item.get('year')}\n"
        f"Rating: {item.get('imdb_rating')}\n"
        f"Genre: {item.get('genre')}\n"
        f"Description: {item.get('description') or item.get('document', 'N/A')}"
        for item in items
    )



def direct_llm_answer(user_message: str, conversation_messages=None) -> str:
    conversation_context = build_conversation_context(conversation_messages)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        messages=[
            {"role": "system", "content": DIRECT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Conversation context:\n{conversation_context}\n\nLatest user message:\n{user_message}",
            },
        ],
    )

    return response.choices[0].message.content


def answer_from_context(user_message: str, items: list[dict], conversation_messages=None) -> str:
    if not items:
        return (
            "Trenutno ne mogu da pronađem dovoljno dobar rezultat u MovieTracker bazi "
            "za taj zahtjev. Probaj sa malo drugačijim opisom, žanrom ili godinom."
        )

    context = format_context(items)
    conversation_context = build_conversation_context(conversation_messages)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        messages=[
            {"role": "system", "content": CONTEXT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Conversation context:\n{conversation_context}\n\n"
                    f"Latest user request:\n{user_message}\n\n"
                    f"MovieTracker database context (ONLY recommend from this list):\n{context}"
                ),
            },
        ],
    )

    return response.choices[0].message.content



def database_search(db: Session, plan: dict) -> list[dict]:
    content_type = plan.get("content_type") or "both"
    genre = plan.get("genre")
    year = plan.get("year")
    min_rating = plan.get("min_rating")
    limit = plan.get("limit") or 5

    results = []

    if content_type in ["movie", "both"]:
        results.extend(
            search_movies_by_filters(db=db, genre=genre, min_rating=min_rating, year=year, limit=limit)
        )

    if content_type in ["tv_show", "both"]:
        results.extend(
            search_tv_shows_by_filters(db=db, genre=genre, min_rating=min_rating, year=year, limit=limit)
        )

    results = sorted(results, key=lambda item: item.get("imdb_rating") or 0, reverse=True)
    return results[:limit]


def semantic_only_search(plan: dict, user_message: str) -> list[dict]:
    semantic_query = plan.get("semantic_query") or user_message
    limit = plan.get("limit") or 5
    min_rating = plan.get("min_rating") or 6.0

    return semantic_search(query=semantic_query, limit=30, min_rating=min_rating)[:limit]


def hybrid_search(db: Session, plan: dict, user_message: str) -> list[dict]:
    semantic_query = plan.get("semantic_query") or user_message
    content_type = plan.get("content_type")
    year = plan.get("year")
    genre = plan.get("genre")
    min_rating = plan.get("min_rating") or 6.0
    limit = plan.get("limit") or 5

    semantic_results = semantic_search(query=semantic_query, limit=50, min_rating=min_rating)

    filtered = []
    for item in semantic_results:
        if content_type and content_type != "both" and item["type"] != content_type:
            continue
        if year is not None and item["year"] != year:
            continue
        if genre and genre.lower() not in (item["genre"] or "").lower():
            continue
        filtered.append(item)

    return filtered[:limit]


def action_answer(user_message: str) -> str:
    return (
        "Mogu da izvršavam akcije kao dodavanje u watchlist, "
        "ali watchlist trenutno još nije prebačen u backend. "
        "Kada dodamo Watchlist model i endpoint, povezaćemo i ovaj dio."
    )



def handle_message(db: Session, user_message: str, conversation_messages=None) -> dict:
    plan = create_plan(user_message, conversation_messages)
    mode = plan.get("mode", "DIRECT_ANSWER")

    print("\n===== AI PLAN =====")
    print(plan)
    print("===================\n")

    if mode == "DIRECT_ANSWER":
        answer = direct_llm_answer(user_message, conversation_messages)

    elif mode == "SEMANTIC_SEARCH":
        items = semantic_only_search(plan, user_message)
        answer = answer_from_context(user_message, items, conversation_messages)

    elif mode == "DATABASE_SEARCH":
        items = database_search(db, plan)
        answer = answer_from_context(user_message, items, conversation_messages)

    elif mode == "HYBRID_SEARCH":
        items = hybrid_search(db, plan, user_message)
        answer = answer_from_context(user_message, items, conversation_messages)

    elif mode == "ACTION":
        answer = action_answer(user_message)

    else:
        answer = direct_llm_answer(user_message, conversation_messages)

    return {
        "category": mode,
        "plan": plan,
        "answer": answer,
    }



def stream_direct_llm_answer(user_message: str, conversation_messages=None):
    conversation_context = build_conversation_context(conversation_messages)

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        stream=True,
        messages=[
            {"role": "system", "content": DIRECT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Conversation context:\n{conversation_context}\n\n"
                    f"Latest user message:\n{user_message}"
                ),
            },
        ],
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def stream_answer_from_context(
    user_message: str,
    items: list[dict],
    conversation_messages=None,
):
    if not items:
        yield (
            "Trenutno ne mogu da pronađem dovoljno dobar rezultat u MovieTracker bazi "
            "za taj zahtjev. Probaj sa malo drugačijim opisom, žanrom ili godinom."
        )
        return

    context = format_context(items)
    conversation_context = build_conversation_context(conversation_messages)

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        stream=True,
        messages=[
            {"role": "system", "content": CONTEXT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Conversation context:\n{conversation_context}\n\n"
                    f"Latest user request:\n{user_message}\n\n"
                    f"MovieTracker database context (ONLY recommend from this list):\n{context}"
                ),
            },
        ],
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def handle_message_stream(db: Session, user_message: str, conversation_messages=None):
    plan = create_plan(user_message, conversation_messages)
    mode = plan.get("mode", "DIRECT_ANSWER")

    print("\n===== AI STREAM PLAN =====")
    print(plan)
    print("==========================\n")

    if mode == "DIRECT_ANSWER":
        yield from stream_direct_llm_answer(user_message, conversation_messages)

    elif mode == "SEMANTIC_SEARCH":
        items = semantic_only_search(plan, user_message)
        yield from stream_answer_from_context(user_message, items, conversation_messages)  # BUG FIX

    elif mode == "DATABASE_SEARCH":
        items = database_search(db, plan)
        yield from stream_answer_from_context(user_message, items, conversation_messages)

    elif mode == "HYBRID_SEARCH":
        items = hybrid_search(db, plan, user_message)
        yield from stream_answer_from_context(user_message, items, conversation_messages)

    elif mode == "ACTION":
        yield action_answer(user_message)

    else:
        yield from stream_direct_llm_answer(user_message, conversation_messages)