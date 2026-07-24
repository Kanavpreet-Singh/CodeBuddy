import json
import uuid
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agent.graph import agent_graph
from agent.tools import set_project_root

router = APIRouter()

DEV_STORAGE_ROOT = Path.cwd() / "generated_projects" / "dev"


class GenerateRequest(BaseModel):
    prompt: str


def _serialize_node_output(node: str, output: dict) -> dict:
    payload = {"node": node, "status": "done"}
    if node == "planner" and output.get("plan") is not None:
        payload["plan"] = output["plan"].model_dump()
    elif node == "architect" and output.get("task_plan") is not None:
        payload["stepCount"] = len(output["task_plan"].implementation_steps)
    elif node == "coder" and output.get("coder_state") is not None:
        coder_state = output["coder_state"]
        payload["step"] = coder_state.current_step_idx
        payload["total"] = len(coder_state.task_plan.implementation_steps)
    return payload


@router.post("/api/generate")
async def generate(req: GenerateRequest):
    run_id = str(uuid.uuid4())
    project_root = DEV_STORAGE_ROOT / run_id
    set_project_root(project_root)

    async def event_stream():
        try:
            async for update in agent_graph.astream({"user_prompt": req.prompt}):
                for node, output in update.items():
                    yield {"event": "node", "data": json.dumps(_serialize_node_output(node, output))}
            yield {
                "event": "done",
                "data": json.dumps({"status": "DONE", "projectRoot": str(project_root)}),
            }
        except Exception as exc:  # surfaces planner/architect/coder failures to the client
            yield {"event": "done", "data": json.dumps({"status": "ERROR", "message": str(exc)})}

    return EventSourceResponse(event_stream())
