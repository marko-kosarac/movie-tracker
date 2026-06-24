import json
import re
from openai import OpenAI
from sqlalchemy.orm import Session

from app.ai.vector_store import semantic_search
from app.ai.tools import search_movies_by_filters, search_tv_shows_by_filters
from app.models.movie import Movie
from app.models.tv_show import TVShow
from app.models.user_list import UserListItem

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


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text


PLANNER_PROMPT = """
You are the planning brain of MovieTracker AI.

Analyze the latest user message together with the conversation context and return a JSON plan.

Return ONLY valid JSON with no markdown fences, no explanation, nothing else.

Schema:
{
  "mode": "DIRECT_ANSWER" | "SEMANTIC_SEARCH" | "DATABASE_SEARCH" | "HYBRID_SEARCH" | "ACTION",
  "content_type": "movie" | "tv_show" | "both" | null,
  "movie_limit": integer | null,
  "tv_show_limit": integer | null,
  "semantic_query": string | null,
  "genre": string | null,
  "year": integer | null,
  "year_from": integer | null,
  "year_to": integer | null,
  "min_rating": number | null,
  "limit": integer,
  "action": "add_to_watchlist" | "add_to_watched" | "remove_from_watchlist" | "remove_from_watched" | "clear_watchlist" | "clear_watched" | null,
  "title": string | null
}

Rules:
- DIRECT_ANSWER is ONLY for: pure factual questions (e.g. "what year was Inception released?", "what is IMDb?"), greetings, or follow-up questions about titles already visible in the conversation context. NEVER use DIRECT_ANSWER when the user wants a list of recommendations.
- SEMANTIC_SEARCH for mood, vibe, atmosphere, similarity, or subgenre descriptions like "psychological thriller", "mind-bending", "dark", "mračno", "napeto", "tužno", "uzbudljivo", "romantično".
- DATABASE_SEARCH for exact constraints: specific genre name, specific year, specific minimum rating — when there is no vague/semantic meaning.
- HYBRID_SEARCH when the request combines any mood/atmosphere/vibe description with any exact filter (year, year range, rating). Also use HYBRID_SEARCH when a genre is mentioned alongside a year range or rating filter.
- ACTION only when the user clearly wants to add/remove from watchlist or mark as watched.
- If user says "best", "top", "good", or "preporuči" without specifying min_rating, set min_rating to 7.0.
- If user does not specify limit, use 5.
- For year constraints: use "year" ONLY for an exact single year (e.g. "iz 2010", "from 2010"). Use "year_from" for "newer than / noviji od / nakon" (e.g. "noviji od 2015" → year_from: 2016). Use "year_to" for "older than / stariji od / prije" (e.g. "stariji od 2000" → year_to: 1999). Never put a range into the "year" field.
- Default content_type to "both" unless user clearly specifies movies or TV shows.

GENRE RULES — very important:
- The "genre" field must ALWAYS be in English, as stored in the database. Never put a local-language word in genre.
- Translate genre names: komedija→Comedy, drama→Drama, horor→Horror, akcija→Action, triler→Thriller, naučna fantastika→Science Fiction, animacija→Animation, dokumentarac→Documentary, romantika→Romance, krimić→Crime, avantura→Adventure, fantazija→Fantasy, misterija→Mystery.
- Mood/atmosphere words are NOT genres. Words like "mračan", "napeto", "uzbudljivo", "romantičan", "smiješan", "tužan", "misteriozno", "dark", "intense" must go into semantic_query, NOT into genre.
- If the user says a genre word (komedija, horor, drama...) alongside a year/rating filter with NO mood words → DATABASE_SEARCH with genre in English.
- If the user says a genre word WITH mood/atmosphere words (e.g. "mračna drama", "napeti triler") → HYBRID_SEARCH: put the translated genre in genre field AND include the mood in semantic_query.
- For semantic_query, always write a rich descriptive English search phrase that fully captures the user's intent including genre and mood.

- CRITICAL LIST DISTINCTION — two completely different lists:
  - "lista gledanja" / "watchlist" = things the user WANTS TO WATCH in the future (not yet watched)
  - "lista gledanih" / "watched" = things the user HAS ALREADY WATCHED

- For ACTION mode, set "action" to one of the six values below. Set "title" to the exact title the user mentioned. Actions that affect "all" do not need a title.

  - "add_to_watchlist": user wants to save something to watch LATER
    Triggers: "dodaj u listu gledanja", "stavi na watchlist", "hoću da gledam X", "zapamti X", "sačuvaj X za gledanje", "add to watchlist", "want to watch X"

  - "add_to_watched": user has ALREADY watched it and wants to mark it
    Triggers: "dodaj u listu gledanih", "označiti kao gledano", "pogledao sam X", "odgledao X", "mark as watched", "already watched X", "add to watched"

  - "remove_from_watchlist": remove a specific title from watchlist
    Triggers: "izbaci X iz liste gledanja", "ukloni X sa watchliste", "obrisi X sa watchliste", "remove X from watchlist"

  - "remove_from_watched": remove a specific title from watched list
    Triggers: "izbaci X iz liste gledanih", "ukloni X iz gledanih", "remove X from watched"

  - "clear_watchlist": remove ALL items from watchlist
    Triggers: "očisti listu gledanja", "obriši sve sa watchliste", "obriši sve što hoću da gledam", "clear watchlist", "izbaci sve iz watchliste"

  - "clear_watched": remove ALL items from watched list
    Triggers: "očisti listu gledanih", "obriši sve gledane", "clear watched list", "izbaci sve iz gledanih"

  - If user says just "obriši sve" / "izbaci sve" without specifying which list, default to "clear_watchlist".

- IMPORTANT: If the user asks for a specific number of movies AND a specific number of TV shows separately (e.g. "jedan film i jedna serija", "2 filma i 3 serije", "one movie and two shows"), set content_type to "both", set movie_limit to the requested movie count, set tv_show_limit to the requested show count, and set limit to their sum. Otherwise leave movie_limit and tv_show_limit as null.
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
                "content": (
                    f"Conversation context:\n{conversation_context}\n\n"
                    f"Latest user message:\n{user_message}"
                ),
            },
        ],
    )

    raw_plan = _strip_json_fence(response.choices[0].message.content)

    try:
        return json.loads(raw_plan)
    except json.JSONDecodeError:
        return {
            "mode": "SEMANTIC_SEARCH",
            "content_type": "both",
            "semantic_query": user_message,
            "genre": None,
            "year": None,
            "min_rating": 6.0,
            "limit": 5,
            "action": None,
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


def format_context(items: list[dict]) -> str:
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
    conversation_context = build_conversation_context(conversation_messages)
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
    conversation_context = build_conversation_context(conversation_messages)
    context = format_context(items)
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


def database_search(db: Session, plan: dict) -> list[dict]:
    content_type = plan.get("content_type") or "both"
    genre = plan.get("genre")
    year = plan.get("year")
    year_from = plan.get("year_from")
    year_to = plan.get("year_to")
    min_rating = plan.get("min_rating")
    limit = plan.get("limit") or 5
    movie_limit = plan.get("movie_limit")
    tv_show_limit = plan.get("tv_show_limit")

    filter_kwargs = dict(genre=_translate_genre(genre), min_rating=min_rating, year=year, year_from=year_from, year_to=year_to)

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


def semantic_only_search(plan: dict, user_message: str) -> list[dict]:
    semantic_query = plan.get("semantic_query") or user_message
    limit = plan.get("limit") or 5
    min_rating = plan.get("min_rating") if plan.get("min_rating") is not None else 6.0

    pool = max(50, limit * 10)
    return semantic_search(query=semantic_query, limit=pool, min_rating=min_rating)[:limit]


def hybrid_search(db: Session, plan: dict, user_message: str) -> list[dict]:
    semantic_query = plan.get("semantic_query") or user_message
    content_type = plan.get("content_type")
    year = plan.get("year")
    year_from = plan.get("year_from")
    year_to = plan.get("year_to")
    genre = _translate_genre(plan.get("genre"))
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

    if search_movie:
        movie = (
            db.query(Movie)
            .filter(Movie.title.ilike(f"%{title}%"))
            .order_by(Movie.imdb_rating.desc().nullslast())
            .first()
        )
        if movie:
            return {"id": movie.id, "type": "movie", "title": movie.title}

    if search_show:
        show = (
            db.query(TVShow)
            .filter(TVShow.title.ilike(f"%{title}%"))
            .order_by(TVShow.imdb_rating.desc().nullslast())
            .first()
        )
        if show:
            return {"id": show.id, "type": "tv_show", "title": show.title}

    return None


def execute_action(db: Session, user_id: int | None, plan: dict) -> str:
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

        db.add(UserListItem(
            user_id=user_id,
            item_id=item["id"],
            item_type=item["type"],
            list_type="watchlist",
        ))
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
        deleted = (
            db.query(UserListItem)
            .filter(
                UserListItem.user_id == user_id,
                UserListItem.list_type == "watchlist",
            )
            .all()
        )

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

        db.add(UserListItem(
            user_id=user_id,
            item_id=item["id"],
            item_type=item["type"],
            list_type="watched",
        ))
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
        deleted = (
            db.query(UserListItem)
            .filter(
                UserListItem.user_id == user_id,
                UserListItem.list_type == "watched",
            )
            .all()
        )

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


def handle_message(db: Session, user_message: str, conversation_messages=None, user_id: int | None = None) -> dict:
    plan = create_plan(user_message, conversation_messages)
    mode = plan.get("mode", "SEMANTIC_SEARCH")

    print("\n===== AI PLAN =====")
    print(plan)
    print("===================\n")

    if mode == "DIRECT_ANSWER":
        answer = _llm_call(_build_direct_messages(user_message, conversation_messages))

    elif mode == "DATABASE_SEARCH":
        items = database_search(db, plan)
        answer = _llm_call(_build_context_messages(user_message, items, conversation_messages))

    elif mode == "HYBRID_SEARCH":
        items = hybrid_search(db, plan, user_message)
        answer = _llm_call(_build_context_messages(user_message, items, conversation_messages))

    elif mode == "ACTION":
        answer = execute_action(db, user_id, plan)

    else:  # SEMANTIC_SEARCH or unknown
        items = semantic_only_search(plan, user_message)
        answer = _llm_call(_build_context_messages(user_message, items, conversation_messages))

    return {"category": mode, "plan": plan, "answer": answer}


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


def handle_message_stream(db: Session, user_message: str, conversation_messages=None, user_id: int | None = None):
    plan = create_plan(user_message, conversation_messages)
    mode = plan.get("mode", "SEMANTIC_SEARCH")

    print("\n===== AI STREAM PLAN =====")
    print(plan)
    print("==========================\n")

    if mode == "DIRECT_ANSWER":
        yield from _llm_stream(_build_direct_messages(user_message, conversation_messages))

    elif mode == "DATABASE_SEARCH":
        items = database_search(db, plan)
        yield from _llm_stream(_build_context_messages(user_message, items, conversation_messages))

    elif mode == "HYBRID_SEARCH":
        items = hybrid_search(db, plan, user_message)
        yield from _llm_stream(_build_context_messages(user_message, items, conversation_messages))

    elif mode == "ACTION":
        yield execute_action(db, user_id, plan)

    else:
        items = semantic_only_search(plan, user_message)
        yield from _llm_stream(_build_context_messages(user_message, items, conversation_messages))
