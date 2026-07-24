from langgraph.graph import END, START, StateGraph

from agent.prompts import architect_prompt, planner_prompt
from agent.states import Plan, State, TaskPlan
from helper.llm import llm


def planner_agent(state: State) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state["user_prompt"]
    resp = llm.with_structured_output(Plan).invoke(
        planner_prompt(user_prompt)
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}


def architect_agent(state: State) -> dict:
    """Creates TaskPlan from Plan."""
    plan: Plan = state["plan"]
    resp = llm.with_structured_output(TaskPlan).invoke(
        architect_prompt(plan=plan.model_dump_json())
    )
    if resp is None:
        raise ValueError("Architect did not return a valid response.")

    resp.plan = plan
    return {"task_plan": resp}


graph_builder = StateGraph(State)
graph_builder.add_node("planner", planner_agent)
graph_builder.add_node("architect", architect_agent)
graph_builder.add_edge(START, "planner")
graph_builder.add_edge("planner", "architect")
graph_builder.add_edge("architect", END)

agent_graph = graph_builder.compile()

if __name__ == "__main__":
    result = agent_graph.invoke({"user_prompt": "A CLI todo app in Python"})
    print(result["task_plan"].model_dump_json(indent=2))
