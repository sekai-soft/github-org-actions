from datetime import datetime
from pydantic import BaseModel


class WorkflowResult(BaseModel):
    name: str
    run_url: str
    created_at: datetime
    status: str


class RepoResult(BaseModel):
    name: str
    repo_url: str
    latest_commit: str
    latest_commit_url: str
    workflows: list[WorkflowResult]


class Result(BaseModel):
    org_name: str
    repos: list[RepoResult]
