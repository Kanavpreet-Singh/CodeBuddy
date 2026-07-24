from typing import Optional, TypedDict

from pydantic import BaseModel, Field


class File(BaseModel):
    path: str = Field(description="The path of the file to be created")
    purpose: str = Field(description="The purpose of the file")


class Plan(BaseModel):
    name: str = Field(description="The name of app to be built")
    description: str = Field(description="A oneline description of the app to be built, e.g. 'A web application for managing personal finances'")
    techstack: str = Field(description="The tech stack to be used for the app, e.g. 'python', 'javascript', 'react', 'flask', etc.")
    features: list[str] = Field(description="A list of features that the app should have, e.g. 'user authentication', 'data visualization', etc.")
    files: list[File] = Field(description="A list of files to be created, each with a 'path' and 'purpose'")


class State(TypedDict):
    user_prompt: str
    plan: Optional[Plan]
