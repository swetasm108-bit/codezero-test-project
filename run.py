import os

import uvicorn

if __name__ == "__main__":
    on_render = "PORT" in os.environ  # Render khud PORT deta hai

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0" if on_render else "127.0.0.1",
        port=int(os.getenv("PORT", 8000)),
        reload=not on_render,
        proxy_headers=on_render,
        forwarded_allow_ips="*" if on_render else None,
    )