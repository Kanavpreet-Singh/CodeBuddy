import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agent.graph import agent_graph
from agent.tools import set_project_root
from server import db
from server.auth import get_current_user_id
from server.storage import app_root, safe_file_path

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str


@router.post("/api/apps")
async def create_app_endpoint(req: GenerateRequest, user_id: str = Depends(get_current_user_id)):
    app_id = await db.create_app(user_id, req.prompt)
    project_root = app_root(user_id, app_id)

    async def event_stream():
        set_project_root(project_root)
        plan_file_purposes: dict[str, str] = {}
        try:
            yield {"event": "created", "data": json.dumps({"id": app_id})}

            async for update in agent_graph.astream({"user_prompt": req.prompt}):
                for node, output in update.items():
                    if node == "planner" and output.get("plan"):
                        plan = output["plan"]
                        plan_file_purposes.update({f.path: f.purpose for f in plan.files})
                        await db.save_plan(
                            app_id, plan.name, plan.description, plan.techstack, plan.features
                        )
                        yield {
                            "event": "node",
                            "data": json.dumps(
                                {"node": "planner", "status": "done", "plan": plan.model_dump()}
                            ),
                        }
                    elif node == "architect" and output.get("task_plan"):
                        task_plan = output["task_plan"]
                        await db.save_task_plan(app_id, task_plan.model_dump())
                        yield {
                            "event": "node",
                            "data": json.dumps(
                                {
                                    "node": "architect",
                                    "status": "done",
                                    "stepCount": len(task_plan.implementation_steps),
                                }
                            ),
                        }
                    elif node == "coder" and output.get("coder_state"):
                        coder_state = output["coder_state"]
                        yield {
                            "event": "node",
                            "data": json.dumps(
                                {
                                    "node": "coder",
                                    "status": "done",
                                    "step": coder_state.current_step_idx,
                                    "total": len(coder_state.task_plan.implementation_steps),
                                }
                            ),
                        }

            files: list[tuple[str, str | None, int]] = []
            if project_root.exists():
                for f in sorted(project_root.glob("**/*")):
                    if f.is_file():
                        rel = str(f.relative_to(project_root)).replace("\\", "/")
                        files.append((rel, plan_file_purposes.get(rel), f.stat().st_size))
            await db.finalize_app(app_id, f"{user_id}/{app_id}", files)
            yield {"event": "done", "data": json.dumps({"status": "DONE", "id": app_id})}
        except Exception as exc:  # persist failure and surface it to the client
            await db.fail_app(app_id, str(exc))
            yield {
                "event": "done",
                "data": json.dumps({"status": "ERROR", "id": app_id, "message": str(exc)}),
            }

    return EventSourceResponse(event_stream())


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
