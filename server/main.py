from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from server import db  # noqa: E402  (import after load_dotenv so env is available)
from server.routers import apps, run  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield
    await db.close_pool()


app = FastAPI(title="CodeBuddy API", lifespan=lifespan)

# Dev-only: allow the Next.js dev server as a fallback direct caller. In the
# normal flow the browser talks only to the Next.js proxy, which forwards here
# with a bearer token, so cross-origin browser calls are not required.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(apps.router)
app.include_router(run.router)


@app.get("/api/healthz")
async def healthz():
    return {"status": "ok"}
