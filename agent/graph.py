import asyncio

from langchain.agents import create_agent
from langchain_core.globals import set_debug, set_verbose
from langgraph.graph import END, START, StateGraph

from agent.prompts import architect_prompt, coder_system_prompt, planner_prompt
from agent.states import CoderState, Plan, State, TaskPlan
from agent.tools import get_current_directory, init_project_root, list_files, read_file, write_file
from helper.llm import default_model_id, make_llm

coder_tools = [read_file, write_file, list_files, get_current_directory]

# gpt-oss-120b occasionally emits reasoning text that Groq rejects as an
# unparseable tool call (output_parse_failed). At temperature 0 that failure is
# deterministic, so we retry a failed coder step with progressively higher
# temperatures to break out of the bad sampling path.
_CODER_RETRY_TEMPERATURES = [0.0, 0.4, 0.8]

_llm_cache: dict[tuple[str, float], object] = {}
_coder_agent_cache: dict[tuple[str, float], object] = {}


def _model_id(state: State) -> str:
    return state.get("model_id") or default_model_id()


def _get_llm(model_id: str, temperature: float = 0.0):
    key = (model_id, temperature)
    if key not in _llm_cache:
        _llm_cache[key] = make_llm(model_id, temperature)
    return _llm_cache[key]


def _get_coder_agent(model_id: str, temperature: float):
    key = (model_id, temperature)
    if key not in _coder_agent_cache:
        _coder_agent_cache[key] = create_agent(
            model=make_llm(model_id, temperature),
            tools=coder_tools,
            system_prompt=coder_system_prompt(),
        )
    return _coder_agent_cache[key]


async def planner_agent(state: State) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state["user_prompt"]
    model = _get_llm(_model_id(state))
    resp = await model.with_structured_output(Plan, method="function_calling").ainvoke(
        planner_prompt(user_prompt)
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}


async def architect_agent(state: State) -> dict:
    """Creates TaskPlan from Plan."""
    plan: Plan = state["plan"]
    model = _get_llm(_model_id(state))
    resp = await model.with_structured_output(TaskPlan, method="function_calling").ainvoke(
        architect_prompt(plan=plan.model_dump_json())
    )
    if resp is None:
        raise ValueError("Architect did not return a valid response.")

    resp.plan = plan
    return {"task_plan": resp}


async def coder_agent(state: State) -> dict:
    """LangGraph tool-using coder agent."""
    model_id = _model_id(state)
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        init_project_root()
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    existing_content = await read_file.ainvoke(current_task.filepath)

    user_prompt = (
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Existing content:\n{existing_content}\n"
        "Use write_file(path, content) to save your changes."
    )

    last_error: Exception | None = None
    for temperature in _CODER_RETRY_TEMPERATURES:
        try:
            await _get_coder_agent(model_id, temperature).ainvoke(
                {"messages": [{"role": "user", "content": user_prompt}]}
            )
            last_error = None
            break
        except Exception as exc:  # retry transient tool-call parse failures
            last_error = exc
    if last_error is not None:
        raise last_error

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


def route_after_coder(state: State) -> str:
    return END if state.get("status") == "DONE" else "coder"


graph_builder = StateGraph(State)
graph_builder.add_node("planner", planner_agent)
graph_builder.add_node("architect", architect_agent)
graph_builder.add_node("coder", coder_agent)
graph_builder.add_edge(START, "planner")
graph_builder.add_edge("planner", "architect")
graph_builder.add_edge("architect", "coder")
graph_builder.add_conditional_edges("coder", route_after_coder, {"coder": "coder", END: END})

agent_graph = graph_builder.compile()


async def _main() -> None:
    set_debug(True)
    set_verbose(True)
    result = await agent_graph.ainvoke({"user_prompt": "A CLI todo app in Python"})
    print(result["status"])


if __name__ == "__main__":
    asyncio.run(_main())
