import os

from fastapi import Header, HTTPException, status

VALID_API_KEYS = set(filter(None, os.getenv("API_KEYS", "dev-key").split(",")))


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing API key")
    return x_api_key