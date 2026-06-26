import json
from openai import OpenAI, APITimeoutError, APIConnectionError, APIStatusError
from sqlalchemy.orm import Session

from app.ai.vector_store import semantic_search, collection
from app.ai.tools import search_movies_by_filters, search_tv_shows_by_filters
from app.models.movie import Movie
from app.models.tv_show import TVShow
from app.models.user_list import UserListItem

client = OpenAI()

MAX_HISTORY = 10

ROUTER_SYSTEM_PROMPT = """
You are the routing brain of MovieTracker AI. Call exactly one function based on the user's message.
When generating direct answers, always reply in the same language the user wrote in.

ROUTING RULES:
- direct_answer: greetings, general movie/TV facts from knowledge, follow-up about titles already in conversation. NEVER for recommendation requests or "does X exist in the database" questions.
- semantic_search: mood, vibe, atmosphere ("psychological thriller", "mind-bending", "dark", "mračno", "napeto", "tužno", "uzbudljivo", "romantično", "similar to X").
- _database_search: exact filters only — specific genre, year, minimum rating. Also when user asks if a specific title exists ("da li ima X", "ima li X u bazi") — set title field.
- _hybrid_search: mood/atmosphere COMBINED with exact filters. Also for genre + mood together ("mračna drama", "napeti triler").
- Action functions: when user wants to add/remove items from their lists.

GENRE — always translate to English: komedija→Comedy, horor→Horror, drama→Drama, akcija→Action, triler→Thriller, naučna fantastika→Science Fiction, animacija→Animation, dokumentarac→Documentary, romantika→Romance, krimić→Crime, avantura→Adventure, fantazija→Fantasy, misterija→Mystery.
Mood/atmosphere words (mračan, napeto, uzbudljivo, tužan, dark, intense) go into semantic_query, NOT genre.

YEAR: use year only for exact single year. Use year_from for "newer than/noviji od/nakon". Use year_to for "older than/stariji od/prije".
LIMITS: default 5. If user says "best/top/preporuči" without specifying rating, use min_rating=7.0.
SPLIT REQUESTS: if user asks for N movies AND M shows separately, set movie_limit=N, tv_show_limit=M, limit=N+M.

LIST NAMES:
- "lista gledanja" / "watchlist" = want to watch (future)
- "lista gledanih" / "watched" = already watched (past)
- "obriši sve" without specifying which list → clear_watchlist

ACTION CONTENT TYPE: For add/remove actions, always set content_type when the user gives a hint:
- "film", "movie" → content_type=movie
- "serija", "series", "show", "emisija" → content_type=tv_show
- If unclear or not mentioned → omit content_type entirely
"""

ROUTER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "direct_answer",
            "description": "Answer directly from knowledge: greetings, general movie/TV facts, follow-up questions about titles already in conversation. Never use for recommendations or database lookups.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string", "description": "Complete response in the user's language. Empty string if question is unrelated to movies/TV."},
                },
                "required": ["answer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": "Search by mood, vibe, atmosphere, or similarity. Use for: psychological, mind-bending, dark, mračno, napeto, tužno, uzbudljivo, similar to X.",
            "parameters": {
                "type": "object",
                "properties": {
                    "semantic_query": {"type": "string", "description": "Rich descriptive English phrase capturing mood and atmosphere"},
                    "content_type": {"type": "string", "enum": ["movie", "tv_show", "both"]},
                    "limit": {"type": "integer"},
                    "min_rating": {"type": "number"},
                    "movie_limit": {"type": "integer"},
                    "tv_show_limit": {"type": "integer"},
                },
                "required": ["semantic_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "_database_search",
            "description": "Search by exact filters: genre, year, rating. Also use when checking if a specific title exists in the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content_type": {"type": "string", "enum": ["movie", "tv_show", "both"]},
                    "genre": {"type": "string", "description": "Genre in English only"},
                    "year": {"type": "integer", "description": "Exact year only, not a range"},
                    "year_from": {"type": "integer", "description": "Minimum year (for newer than / noviji od)"},
                    "year_to": {"type": "integer", "description": "Maximum year (for older than / stariji od)"},
                    "min_rating": {"type": "number"},
                    "limit": {"type": "integer"},
                    "movie_limit": {"type": "integer"},
                    "tv_show_limit": {"type": "integer"},
                    "title": {"type": "string", "description": "Title to look up when user asks if it exists in the database"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "_hybrid_search",
            "description": "Mood/atmosphere combined with exact filters (year, rating, genre). Use for 'mračna drama', 'napeti triler', mood + year/rating.",
            "parameters": {
                "type": "object",
                "properties": {
                    "semantic_query": {"type": "string", "description": "Rich descriptive English phrase"},
                    "content_type": {"type": "string", "enum": ["movie", "tv_show", "both"]},
                    "genre": {"type": "string"},
                    "year": {"type": "integer"},
                    "year_from": {"type": "integer"},
                    "year_to": {"type": "integer"},
                    "min_rating": {"type": "number"},
                    "limit": {"type": "integer"},
                    "movie_limit": {"type": "integer"},
                    "tv_show_limit": {"type": "integer"},
                },
                "required": ["semantic_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_watchlist",
            "description": "Add a movie or TV show to the user's watchlist (to watch later)",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content_type": {"type": "string", "enum": ["movie", "tv_show"], "description": "Set to 'tv_show' if user says 'serija/series/show', 'movie' if user says 'film/movie'. Omit if unclear."},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_watched",
            "description": "Mark a movie or TV show as already watched",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content_type": {"type": "string", "enum": ["movie", "tv_show"], "description": "Set to 'tv_show' if user says 'serija/series/show', 'movie' if user says 'film/movie'. Omit if unclear."},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_watchlist",
            "description": "Remove a specific movie or TV show from the watchlist",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content_type": {"type": "string", "enum": ["movie", "tv_show"], "description": "Set to 'tv_show' if user says 'serija/series/show', 'movie' if user says 'film/movie'. Omit if unclear."},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_watched",
            "description": "Remove a specific movie or TV show from the watched list",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content_type": {"type": "string", "enum": ["movie", "tv_show"], "description": "Set to 'tv_show' if user says 'serija/series/show', 'movie' if user says 'film/movie'. Omit if unclear."},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clear_watchlist",
            "description": "Remove ALL items from the user's watchlist",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clear_watched",
            "description": "Remove ALL items from the user's watched list",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

ACTION_FUNCTION_NAMES = {
    "add_to_watchlist", "add_to_watched",
    "remove_from_watchlist", "remove_from_watched",
    "clear_watchlist", "clear_watched",
}

DIRECT_SYSTEM_PROMPT = """
You are MovieTracker AI assistant. Always reply in the same language the user wrote in.

You specialize in movies, TV shows, and the MovieTracker app.

You may answer factual questions and follow-up questions about titles already mentioned
in the conversation context. If the user asks for recommendations or a list of movies/shows,
tell them you are searching the database — do NOT invent any titles.

If the question is unrelated to movies, TV shows, or MovieTracker, politely redirect.

CRITICAL: Never invent or suggest any movie or TV title not explicitly provided to you.
"""

CONTEXT_SYSTEM_PROMPT = """
You are MovieTracker AI assistant. Always reply in the same language the user wrote in.

Your job is to recommend movies and TV shows STRICTLY from the provided MovieTracker database context.

Rules:
- NEVER mention, suggest, or recommend any movie or TV show not listed in the database context.
- Do not invent titles, directors, actors, ratings, or plot details.
- Do not say "you might also like X" if X is not in the context.
- Choose the best 3–5 results based on relevance to the request and IMDb rating.
- For each recommendation, briefly state: title, year, IMDb rating, and why it fits the request.
- If context is empty or has no relevant results, say so honestly — do not invent alternatives.
- You may use conversation context to understand follow-up questions.
"""

_GENRE_TRANSLATIONS = {
    "komedija": "Comedy", "horor": "Horror", "drama": "Drama",
    "akcija": "Action", "triler": "Thriller", "trileri": "Thriller",
    "naučna fantastika": "Science Fiction", "sci-fi": "Science Fiction",
    "animacija": "Animation", "dokumentarac": "Documentary",
    "romantika": "Romance", "krimić": "Crime", "krimi": "Crime",
    "avantura": "Adventure", "fantazija": "Fantasy", "misterija": "Mystery",
    "biografija": "Biography", "istorija": "History", "sport": "Sport",
    "mjuzikl": "Musical", "vestern": "Western",
}


def _translate_genre(genre: str | None) -> str | None:
    if not genre:
        return genre
    return _GENRE_TRANSLATIONS.get(genre.lower().strip(), genre)


def _build_conversation_context(conversation_messages=None) -> str:
    if not conversation_messages:
        return ""
    lines = []
    for msg in conversation_messages[-MAX_HISTORY:]:
        role = getattr(msg, "role", None) or msg.get("role")
        content = getattr(msg, "content", None) or msg.get("content")
        if role and content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _route_request(user_message: str, conversation_messages=None) -> tuple[str, dict]:
    conversation_context = _build_conversation_context(conversation_messages)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Conversation context:\n{conversation_context}\n\n"
                    f"Latest user message:\n{user_message}"
                ),
            },
        ],
        tools=ROUTER_TOOLS,
        tool_choice="required",
    )
    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    return tool_call.function.name, args


def _format_context(items: list[dict]) -> str:
    if not items:
        return "Nema rezultata u bazi."
    return "\n\n".join(
        f"Title: {item.get('title')}\n"
        f"Type: {item.get('type')}\n"
        f"Year: {item.get('year')}\n"
        f"Rating: {item.get('imdb_rating')}\n"
        f"Genre: {item.get('genre')}\n"
        f"Actors: {item.get('actors') or 'N/A'}\n"
        f"Description: {item.get('description') or item.get('document', 'N/A')}"
        for item in items
    )


def _build_direct_messages(user_message: str, conversation_messages=None) -> list:
    conversation_context = _build_conversation_context(conversation_messages)
    return [
        {"role": "system", "content": DIRECT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Conversation context:\n{conversation_context}\n\n"
                f"Latest user message:\n{user_message}"
            ),
        },
    ]


def _build_context_messages(user_message: str, items: list[dict], conversation_messages=None) -> list:
    conversation_context = _build_conversation_context(conversation_messages)
    context = _format_context(items)
    return [
        {"role": "system", "content": CONTEXT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Conversation context:\n{conversation_context}\n\n"
                f"Latest user request:\n{user_message}\n\n"
                f"MovieTracker database context (ONLY recommend from this list):\n{context}"
            ),
        },
    ]


def _args_to_plan(args: dict) -> dict:
    return {
        "content_type": args.get("content_type", "both"),
        "limit": args.get("limit", 5),
        "min_rating": args.get("min_rating", 6.0),
        "semantic_query": args.get("semantic_query"),
        "genre": _translate_genre(args.get("genre")),
        "year": args.get("year"),
        "year_from": args.get("year_from"),
        "year_to": args.get("year_to"),
        "movie_limit": args.get("movie_limit"),
        "tv_show_limit": args.get("tv_show_limit"),
        "title": args.get("title"),
    }


def _database_search(db: Session, plan: dict) -> list[dict]:
    content_type = plan.get("content_type")
    limit = plan.get("limit")
    movie_limit = plan.get("movie_limit")
    tv_show_limit = plan.get("tv_show_limit")
    filter_kwargs = dict(
        genre=plan.get("genre"),
        min_rating=plan.get("min_rating"),
        year=plan.get("year"),
        year_from=plan.get("year_from"),
        year_to=plan.get("year_to"),
        title=plan.get("title"),
    )

    if movie_limit is not None or tv_show_limit is not None:
        results = []
        if movie_limit:
            results.extend(search_movies_by_filters(db=db, limit=movie_limit, **filter_kwargs))
        if tv_show_limit:
            results.extend(search_tv_shows_by_filters(db=db, limit=tv_show_limit, **filter_kwargs))
        return results

    fetch_limit = limit * 3
    results = []
    if content_type in ["movie", "both"]:
        results.extend(search_movies_by_filters(db=db, limit=fetch_limit, **filter_kwargs))
    if content_type in ["tv_show", "both"]:
        results.extend(search_tv_shows_by_filters(db=db, limit=fetch_limit, **filter_kwargs))

    results.sort(key=lambda item: item.get("imdb_rating") or 0, reverse=True)
    return results[:limit]


def _semantic_only_search(plan: dict, user_message: str) -> list[dict]:
    semantic_query = plan.get("semantic_query") or user_message
    limit = plan.get("limit") or 5
    min_rating = plan.get("min_rating") if plan.get("min_rating") is not None else 6.0
    pool = max(50, limit * 10)
    return semantic_search(query=semantic_query, limit=pool, min_rating=min_rating)[:limit]


def _hybrid_search(db: Session, plan: dict, user_message: str) -> list[dict]:
    semantic_query = plan.get("semantic_query") or user_message
    content_type = plan.get("content_type")
    year = plan.get("year")
    year_from = plan.get("year_from")
    year_to = plan.get("year_to")
    genre = plan.get("genre")
    min_rating = plan.get("min_rating") if plan.get("min_rating") is not None else 6.0
    limit = plan.get("limit") or 5
    movie_limit = plan.get("movie_limit")
    tv_show_limit = plan.get("tv_show_limit")

    semantic_results = semantic_search(query=semantic_query, limit=1000, min_rating=min_rating)

    filtered = []
    for item in semantic_results:
        item_year = item.get("year") or 0
        if year is not None and item_year != year:
            continue
        if year_from is not None and item_year < year_from:
            continue
        if year_to is not None and item_year > year_to:
            continue
        if genre and genre.lower() not in (item["genre"] or "").lower():
            continue
        filtered.append(item)

    if movie_limit is not None or tv_show_limit is not None:
        movies = [i for i in filtered if i["type"] == "movie"][:movie_limit or 0]
        shows = [i for i in filtered if i["type"] == "tv_show"][:tv_show_limit or 0]
        return movies + shows

    if content_type and content_type != "both":
        filtered = [i for i in filtered if i["type"] == content_type]

    return filtered[:limit]


def _find_item_by_title(db: Session, title: str, content_type: str | None) -> dict | None:
    search_movie = content_type in (None, "both", "movie")
    search_show = content_type in (None, "both", "tv_show")

    candidates = []

    if search_movie:
        for movie in db.query(Movie).filter(Movie.title.ilike(f"%{title}%")).all():
            candidates.append({"id": movie.id, "type": "movie", "title": movie.title})

    if search_show:
        for show in db.query(TVShow).filter(TVShow.title.ilike(f"%{title}%")).all():
            candidates.append({"id": show.id, "type": "tv_show", "title": show.title})

    if not candidates:
        return None

    search_lower = title.lower()

    def _match_score(c: dict) -> tuple:
        t = c["title"].lower()
        if t == search_lower:
            return (0, 0)
        # ratio of search term length to result title length — higher = better match
        ratio = len(search_lower) / max(len(t), 1)
        return (1, -ratio)

    candidates.sort(key=_match_score)
    return candidates[0]


def _execute_action(db: Session, user_id: int | None, plan: dict) -> str:
    if not user_id:
        return "Moraš biti prijavljen da bi upravljao listama."

    action = plan.get("action")
    title = plan.get("title")
    content_type = plan.get("content_type")

    if action == "add_to_watchlist":
        if not title:
            return "Navedi naziv filma ili serije koji želiš dodati u listu gledanja."
        item = _find_item_by_title(db, title, content_type)
        if not item:
            return f"Nisam pronašao '{title}' u bazi. Provjeri naziv i pokušaj ponovo."
        existing = db.query(UserListItem).filter(
            UserListItem.user_id == user_id,
            UserListItem.item_id == item["id"],
            UserListItem.item_type == item["type"],
        ).first()
        if existing:
            if existing.list_type == "watchlist":
                return f"'{item['title']}' je već u tvojoj listi gledanja."
            return f"'{item['title']}' je već u tvojoj listi pogledanog."
        db.add(UserListItem(user_id=user_id, item_id=item["id"], item_type=item["type"], list_type="watchlist"))
        db.commit()
        kind = "film" if item["type"] == "movie" else "serija"
        return f"✓ '{item['title']}' ({kind}) je dodan u tvoju listu gledanja."

    if action == "remove_from_watchlist":
        if not title:
            return "Navedi naziv filma ili serije koji želiš izbaciti iz liste gledanja."
        item = _find_item_by_title(db, title, content_type)
        if not item:
            return f"Nisam pronašao '{title}' u bazi. Provjeri naziv i pokušaj ponovo."
        entry = db.query(UserListItem).filter(
            UserListItem.user_id == user_id,
            UserListItem.item_id == item["id"],
            UserListItem.item_type == item["type"],
            UserListItem.list_type == "watchlist",
        ).first()
        if not entry:
            return f"'{item['title']}' nije u tvojoj listi gledanja."
        db.delete(entry)
        db.commit()
        return f"✓ '{item['title']}' je uklonjen iz tvoje liste gledanja."

    if action == "clear_watchlist":
        deleted = db.query(UserListItem).filter(
            UserListItem.user_id == user_id,
            UserListItem.list_type == "watchlist",
        ).all()
        if not deleted:
            return "Tvoja lista gledanja je već prazna."
        count = len(deleted)
        for entry in deleted:
            db.delete(entry)
        db.commit()
        return f"✓ Lista gledanja je očišćena — uklonjeno {count} {'stavki' if count != 1 else 'stavka'}."

    if action == "add_to_watched":
        if not title:
            return "Navedi naziv filma ili serije koji želiš označiti kao pogledano."
        item = _find_item_by_title(db, title, content_type)
        if not item:
            return f"Nisam pronašao '{title}' u bazi. Provjeri naziv i pokušaj ponovo."
        existing = db.query(UserListItem).filter(
            UserListItem.user_id == user_id,
            UserListItem.item_id == item["id"],
            UserListItem.item_type == item["type"],
        ).first()
        if existing:
            if existing.list_type == "watched":
                return f"'{item['title']}' je već u tvojoj listi gledanih."
            existing.list_type = "watched"
            db.commit()
            kind = "film" if item["type"] == "movie" else "serija"
            return f"✓ '{item['title']}' ({kind}) je premješten iz liste gledanja u listu gledanih."
        db.add(UserListItem(user_id=user_id, item_id=item["id"], item_type=item["type"], list_type="watched"))
        db.commit()
        kind = "film" if item["type"] == "movie" else "serija"
        return f"✓ '{item['title']}' ({kind}) je dodan u tvoju listu gledanih."

    if action == "remove_from_watched":
        if not title:
            return "Navedi naziv filma ili serije koji želiš izbaciti iz liste gledanih."
        item = _find_item_by_title(db, title, content_type)
        if not item:
            return f"Nisam pronašao '{title}' u bazi. Provjeri naziv i pokušaj ponovo."
        entry = db.query(UserListItem).filter(
            UserListItem.user_id == user_id,
            UserListItem.item_id == item["id"],
            UserListItem.item_type == item["type"],
            UserListItem.list_type == "watched",
        ).first()
        if not entry:
            return f"'{item['title']}' nije u tvojoj listi gledanih."
        db.delete(entry)
        db.commit()
        return f"✓ '{item['title']}' je uklonjen iz tvoje liste gledanih."

    if action == "clear_watched":
        deleted = db.query(UserListItem).filter(
            UserListItem.user_id == user_id,
            UserListItem.list_type == "watched",
        ).all()
        if not deleted:
            return "Tvoja lista gledanih je već prazna."
        count = len(deleted)
        for entry in deleted:
            db.delete(entry)
        db.commit()
        return f"✓ Lista gledanih je očišćena — uklonjeno {count} {'stavki' if count != 1 else 'stavka'}."

    return "Nepoznata akcija."


def _llm_call(messages: list) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        messages=messages,
    )
    return response.choices[0].message.content


def _llm_stream(messages: list):
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        stream=True,
        messages=messages,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def _execute_search(func_name: str, plan: dict, db: Session, user_message: str) -> list[dict]:
    if func_name == "semantic_search":
        return _semantic_only_search(plan, user_message) if collection.count() > 0 else _database_search(db, plan)
    if func_name == "_database_search":
        return _database_search(db, plan)
    return _hybrid_search(db, plan, user_message) if collection.count() > 0 else _database_search(db, plan)


def handle_message(db: Session, user_message: str, conversation_messages=None, user_id: int | None = None) -> dict:
    try:
        conversation_messages = (conversation_messages or [])[-MAX_HISTORY:]
        func_name, args = _route_request(user_message, conversation_messages)

        if func_name == "direct_answer":
            answer = args.get("answer") or _llm_call(_build_direct_messages(user_message, conversation_messages))
            return {"category": "DIRECT_ANSWER", "answer": answer}

        if func_name in ACTION_FUNCTION_NAMES:
            action_plan = {"action": func_name, "title": args.get("title"), "content_type": args.get("content_type")}
            return {"category": "ACTION", "answer": _execute_action(db, user_id, action_plan)}

        plan = _args_to_plan(args)
        items = _execute_search(func_name, plan, db, user_message)
        answer = _llm_call(_build_context_messages(user_message, items, conversation_messages))
        return {"category": func_name.upper(), "answer": answer}

    except (APITimeoutError, APIConnectionError):
        return {"category": "ERROR", "plan": {}, "answer": "AI servis trenutno nije dostupan. Provjeri internet konekciju i pokušaj ponovo."}
    except APIStatusError as e:
        return {"category": "ERROR", "plan": {}, "answer": f"Greška AI servisa ({e.status_code}). Pokušaj ponovo za koji trenutak."}


def handle_message_stream(db: Session, user_message: str, conversation_messages=None, user_id: int | None = None):
    try:
        conversation_messages = (conversation_messages or [])[-MAX_HISTORY:]
        func_name, args = _route_request(user_message, conversation_messages)

        if func_name == "direct_answer":
            answer = args.get("answer")
            if answer:
                yield answer
            else:
                yield from _llm_stream(_build_direct_messages(user_message, conversation_messages))
            return

        if func_name in ACTION_FUNCTION_NAMES:
            action_plan = {"action": func_name, "title": args.get("title"), "content_type": args.get("content_type")}
            yield _execute_action(db, user_id, action_plan)
            return

        plan = _args_to_plan(args)
        items = _execute_search(func_name, plan, db, user_message)
        yield from _llm_stream(_build_context_messages(user_message, items, conversation_messages))

    except (APITimeoutError, APIConnectionError):
        yield "AI servis trenutno nije dostupan. Provjeri internet konekciju i pokušaj ponovo."
    except APIStatusError as e:
        yield f"Greška AI servisa ({e.status_code}). Pokušaj ponovo za koji trenutak."
