from datetime import datetime
from pydantic import BaseModel


class WorkflowResult(BaseModel):
    name: str
    created_at: datetime
    status: str


class RepoResult(BaseModel):
    name: str
    workflows: list[WorkflowResult]
