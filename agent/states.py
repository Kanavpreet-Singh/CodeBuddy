from typing import Optional, TypedDict

from pydantic import BaseModel, ConfigDict, Field


class File(BaseModel):
    path: str = Field(description="The path of the file to be created")
    purpose: str = Field(description="The purpose of the file")


class Plan(BaseModel):
    name: str = Field(description="The name of app to be built")
    description: str = Field(description="A oneline description of the app to be built, e.g. 'A web application for managing personal finances'")
    techstack: str = Field(description="The tech stack to be used for the app, e.g. 'python', 'javascript', 'react', 'flask', etc.")
    features: list[str] = Field(description="A list of features that the app should have, e.g. 'user authentication', 'data visualization', etc.")
    files: list[File] = Field(description="A list of files to be created, each with a 'path' and 'purpose'")


class ImplementationTask(BaseModel):
    filepath: str = Field(description="The path to the file to be modified")
    task_description: str = Field(description="A detailed description of the task to be performed on the file, e.g. 'add user authentication', 'implement data processing logic', etc.")


class TaskPlan(BaseModel):
    implementation_steps: list[ImplementationTask] = Field(description="A list of steps to be taken to implement the task")
    plan: Optional[Plan] = Field(default=None, description="The original project plan this task plan was derived from")
    model_config = ConfigDict(extra="allow")


class State(TypedDict):
    user_prompt: str
    plan: Optional[Plan]
    task_plan: Optional[TaskPlan]
