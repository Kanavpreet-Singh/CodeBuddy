from fastapi import FastAPI

from server.routers import generate

app = FastAPI(title="CodeBuddy API")
app.include_router(generate.router)


@app.get("/api/healthz")
async def healthz():
    return {"status": "ok"}
