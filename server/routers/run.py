import os

from fastapi import APIRouter, Depends, HTTPException

from server import db, sandbox
from server.auth import get_current_user_id
from server.ratelimit import rate_limit_run
from server.storage import read_app_files

router = APIRouter()


@router.post("/api/apps/{app_id}/run")
async def run_app_endpoint(app_id: str, user_id: str = Depends(rate_limit_run)):
    if not os.environ.get("E2B_API_KEY"):
        raise HTTPException(status_code=503, detail="Run mode is not configured (missing E2B_API_KEY)")

    app = await db.get_app(app_id, user_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    files = read_app_files(user_id, app_id)
    if not files:
        raise HTTPException(status_code=400, detail="No files to run")

    try:
        result = await sandbox.run_app(files)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sandbox run failed: {exc}")

    expires_at = None
    if result.kind == "web":
        expires_at = await db.create_sandbox_run(
            app_id, result.sandbox_id, result.preview_url, "RUNNING", sandbox.get_timeout()
        )

    return {
        "kind": result.kind,
        "sandboxId": result.sandbox_id,
        "previewUrl": result.preview_url,
        "output": result.output,
        "port": result.port,
        "expiresAt": expires_at.isoformat() if expires_at else None,
    }


@router.post("/api/apps/{app_id}/run/{sandbox_id}/stop")
async def stop_run_endpoint(
    app_id: str, sandbox_id: str, user_id: str = Depends(get_current_user_id)
):
    app = await db.get_app(app_id, user_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    await sandbox.stop_sandbox(sandbox_id)
    await db.mark_sandbox_stopped(sandbox_id)
    return {"status": "stopped"}
