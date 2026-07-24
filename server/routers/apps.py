import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.callbacks import get_usage_metadata_callback
from pydantic import BaseModel

from agent.graph import agent_graph, fix_agent
from agent.tools import set_project_root
from helper.llm import available_models, default_model_id, estimate_cost_inr
from server import db, progress
from server.auth import get_current_user_id
from server.ratelimit import rate_limit_generation
from server.storage import app_root, safe_file_path

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None


class FixRequest(BaseModel):
    feedback: str
    runOutput: Optional[str] = None
    model: Optional[str] = None


@router.get("/api/models")
async def list_models_endpoint(user_id: str = Depends(get_current_user_id)):
    return {"models": available_models(), "default": default_model_id()}


def _aggregate_usage(usage_metadata: dict) -> dict:
    """Sums input/output tokens across all models used in a run."""
    total_in = sum(v.get("input_tokens", 0) for v in usage_metadata.values())
    total_out = sum(v.get("output_tokens", 0) for v in usage_metadata.values())
    return {"input_tokens": total_in, "output_tokens": total_out}


async def _run_generation(app_id: str, user_id: str, prompt: str, model_id: str) -> None:
    """Runs the agent graph in the background, writing progress as each stage
    completes so GET /api/apps/{id}/progress can report it to a polling client."""
    project_root = app_root(user_id, app_id)
    set_project_root(project_root)
    plan_file_purposes: dict[str, str] = {}

    try:
        with get_usage_metadata_callback() as usage_cb:
            async for update in agent_graph.astream({"user_prompt": prompt, "model_id": model_id}):
                for node, output in update.items():
                    if node == "planner" and output.get("plan"):
                        plan = output["plan"]
                        plan_file_purposes.update({f.path: f.purpose for f in plan.files})
                        await db.save_plan(
                            app_id, plan.name, plan.description, plan.techstack, plan.features
                        )
                        progress.set_progress(
                            app_id, stage="architecting", status="ARCHITECTING", plan=plan.model_dump()
                        )
                    elif node == "architect" and output.get("task_plan"):
                        task_plan = output["task_plan"]
                        await db.save_task_plan(app_id, task_plan.model_dump())
                        progress.set_progress(
                            app_id,
                            stage="coding",
                            status="CODING",
                            stepCount=len(task_plan.implementation_steps),
                            codingStep=0,
                        )
                    elif node == "coder" and output.get("coder_state"):
                        coder_state = output["coder_state"]
                        progress.set_progress(
                            app_id,
                            stage="coding",
                            status="CODING",
                            codingStep=coder_state.current_step_idx,
                            codingTotal=len(coder_state.task_plan.implementation_steps),
                        )

        files: list[tuple[str, str | None, int]] = []
        if project_root.exists():
            for f in sorted(project_root.glob("**/*")):
                if f.is_file():
                    rel = str(f.relative_to(project_root)).replace("\\", "/")
                    files.append((rel, plan_file_purposes.get(rel), f.stat().st_size))
        await db.finalize_app(app_id, f"{user_id}/{app_id}", files)

        usage = _aggregate_usage(usage_cb.usage_metadata)
        cost = estimate_cost_inr(model_id, usage["input_tokens"], usage["output_tokens"])
        print(
            f"[usage] app={app_id} model={model_id} "
            f"in={usage['input_tokens']} out={usage['output_tokens']} est_inr={cost}"
        )
        progress.set_progress(
            app_id,
            stage="done",
            status="DONE",
            usage={
                "model": model_id,
                "inputTokens": usage["input_tokens"],
                "outputTokens": usage["output_tokens"],
                "estimatedCostInr": cost,
            },
        )
    except Exception as exc:  # persist failure and surface it to the client
        await db.fail_app(app_id, str(exc))
        progress.set_progress(app_id, stage="error", status="ERROR", message=str(exc))


@router.post("/api/apps")
async def create_app_endpoint(req: GenerateRequest, user_id: str = Depends(rate_limit_generation)):
    valid_ids = {m["id"] for m in available_models()}
    model_id = req.model if req.model in valid_ids else default_model_id()

    app_id = await db.create_app(user_id, req.prompt)
    progress.set_progress(app_id, stage="planning", status="PLANNING")

    task = asyncio.create_task(_run_generation(app_id, user_id, req.prompt, model_id))
    progress.track_task(task)

    return {"id": app_id, "status": "PLANNING", "model": model_id}


async def _run_fix(
    app_id: str, user_id: str, storage_path: str, feedback: str, run_output: Optional[str], model_id: str
) -> None:
    """Runs the fixer agent in the background against the app's existing files."""
    project_root = app_root(user_id, app_id)
    set_project_root(project_root)

    try:
        with get_usage_metadata_callback() as usage_cb:
            await fix_agent(feedback, run_output, model_id)

        files: list[tuple[str, str | None, int]] = []
        if project_root.exists():
            for f in sorted(project_root.glob("**/*")):
                if f.is_file():
                    rel = str(f.relative_to(project_root)).replace("\\", "/")
                    files.append((rel, None, f.stat().st_size))
        await db.finalize_app(app_id, storage_path, files)

        usage = _aggregate_usage(usage_cb.usage_metadata)
        cost = estimate_cost_inr(model_id, usage["input_tokens"], usage["output_tokens"])
        print(
            f"[usage] app={app_id} fix model={model_id} "
            f"in={usage['input_tokens']} out={usage['output_tokens']} est_inr={cost}"
        )
        progress.set_progress(
            app_id,
            stage="done",
            status="DONE",
            usage={
                "model": model_id,
                "inputTokens": usage["input_tokens"],
                "outputTokens": usage["output_tokens"],
                "estimatedCostInr": cost,
            },
        )
    except Exception as exc:
        await db.fail_app(app_id, str(exc))
        progress.set_progress(app_id, stage="error", status="ERROR", message=str(exc))


@router.post("/api/apps/{app_id}/fix")
async def fix_app_endpoint(
    app_id: str, req: FixRequest, user_id: str = Depends(rate_limit_generation)
):
    app = await db.get_app(app_id, user_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    if app["status"] not in ("DONE", "ERROR"):
        raise HTTPException(status_code=409, detail="This app is still building — wait for it to finish first")
    if not req.feedback.strip():
        raise HTTPException(status_code=400, detail="Describe what's wrong before asking for a fix")

    valid_ids = {m["id"] for m in available_models()}
    model_id = req.model if req.model in valid_ids else default_model_id()
    storage_path = app.get("storagePath") or f"{user_id}/{app_id}"

    progress.set_progress(app_id, stage="fixing", status="FIXING")
    task = asyncio.create_task(
        _run_fix(app_id, user_id, storage_path, req.feedback, req.runOutput, model_id)
    )
    progress.track_task(task)

    return {"id": app_id, "status": "FIXING", "model": model_id}


@router.get("/api/apps/{app_id}/progress")
async def get_progress_endpoint(app_id: str, user_id: str = Depends(get_current_user_id)):
    # Verify ownership first — the in-memory progress store is keyed only by
    # app_id, so it must never be served without confirming this user owns it.
    app = await db.get_app(app_id, user_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    live = progress.get_progress(app_id)
    if live is not None:
        return live

    # Not tracked in memory (server restarted mid-build, or this app finished
    # in a previous process lifetime) — reconstruct a terminal state from the DB.
    status = app["status"]
    if status == "DONE":
        return {"stage": "done", "status": "DONE"}
    if status == "ERROR":
        return {"stage": "error", "status": "ERROR", "message": app.get("errorMessage")}
    return {"stage": "unknown", "status": status}


@router.get("/api/apps")
async def list_apps_endpoint(user_id: str = Depends(get_current_user_id)):
    return await db.list_apps(user_id)


@router.get("/api/apps/{app_id}")
async def get_app_endpoint(app_id: str, user_id: str = Depends(get_current_user_id)):
    app = await db.get_app(app_id, user_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    features = app.get("features")
    app["features"] = json.loads(features) if isinstance(features, str) else (features or [])
    app["files"] = await db.get_app_files(app_id)
    return app


@router.get("/api/apps/{app_id}/files")
async def get_file_endpoint(app_id: str, path: str, user_id: str = Depends(get_current_user_id)):
    app = await db.get_app(app_id, user_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    try:
        file_path = safe_file_path(user_id, app_id, path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return {"path": path, "content": file_path.read_text(encoding="utf-8")}
