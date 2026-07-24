from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routers import generate

app = FastAPI(title="CodeBuddy API")

# Dev-only: allow the Next.js dev server to call the API directly (Milestone 2, no auth yet).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)


@app.get("/api/healthz")
async def healthz():
    return {"status": "ok"}
