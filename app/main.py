import random
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse

from app.auth import verify_api_key
from app.rate_limiter import rate_limit

app = FastAPI(title="CodeZero Quotes API")

BASE_DIR = Path(__file__).parent

QUOTES = [
    {"text": "First, solve the problem. Then, write the code.", "author": "John Johnson"},
    {"text": "Simplicity is the soul of efficiency.", "author": "Austin Freeman"},
    {"text": "Make it work, make it right, make it fast.", "author": "Kent Beck"},
    {"text": "Talk is cheap. Show me the code.", "author": "Linus Torvalds"},
    {"text": "Programs must be written for people to read.", "author": "Harold Abelson"},
    {"text": "Code is like humor. When you have to explain it, it's bad.", "author": "Cory House"},
    {"text": "The best way to predict the future is to invent it.", "author": "Alan Kay"},
    {"text": "Stay hungry, stay foolish.", "author": "Steve Jobs"},
]


@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


# Public endpoint: 10 requests per minute per user
@app.get("/quote", dependencies=[Depends(rate_limit(10, 60))])
async def quote():
    return random.choice(QUOTES)


# Protected endpoint: needs API key, 5 requests per minute
@app.get("/protected", dependencies=[Depends(rate_limit(5, 60)), Depends(verify_api_key)])
async def protected():
    return {"message": "secret data"}