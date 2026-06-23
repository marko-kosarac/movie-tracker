from typing import List, Literal
import os

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

router = APIRouter(prefix="/ai", tags=["AI"])
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


SYSTEM_PROMPT = """
            Ti si MovieTracker AI asistent.
            Budi prijatan i strpljiv.
            Pomažeš korisniku da pronađe filmove i serije.
            Odgovaraj na srpskom jeziku.
            Ne forsiraj filmove i serije, ali ako ti bude postavljeno pitanje nevezano za filmove i serije,
            nemoj odgovoriti.
            Izvini se korisniku i reci mu da nisi tu da bi odgovarao na takva pitanja, a zatim ga pitaj da li mu treba
            pomoć vezano za filmove i serije.
            Ako korisnik traži preporuku, predloži 3 opcije, osim ako naglasi koliko opcija želi.
            Ako nemaš dovoljno informacija, postavi jedno kratko pitanje.
            Nemoj tvrditi da je neki film u MovieTracker bazi ako ti baza nije data.
            Ako nešto ne znaš ili nisi siguran, odgovori tako, ne izmišljaj podatke.
            """


def build_messages(request_messages: List[ChatMessage]):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    for message in request_messages:
        messages.append(
            {
                "role": message.role,
                "content": message.content,
            }
        )

    return messages


@router.post("/chat")
def chat_with_ai(request: ChatRequest):
    messages = build_messages(request.messages)

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        max_tokens=500,
    )

    return {
        "answer": response.choices[0].message.content
    }


@router.post("/chat-stream")
def chat_with_ai_stream(request: ChatRequest):
    messages = build_messages(request.messages)

    def generate():
        stream = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=500,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content

            if delta:
                yield delta

    return StreamingResponse(generate(), media_type="text/plain")