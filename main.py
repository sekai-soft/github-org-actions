from typing import Annotated
from fastapi import FastAPI, Query
from pydantic_settings import BaseSettings, SettingsConfigDict
from github import Github, Auth
from github_org_actions.models import RepoResult
from github_org_actions.github import get_repo_res


class Settings(BaseSettings):
    github_token: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
app = FastAPI()
auth = Auth.Token(settings.github_token)
github = Github(auth=auth)


@app.get("/api/{org}")
async def _api(org: str, e: Annotated[list[str], Query()] = []) -> list[RepoResult]:
    org = github.get_organization(org)
    repos = org.get_repos(type="public")
    res = []
    for repo in repos:
        repo_res = get_repo_res(repo, e)
        if repo_res:
            res.append(repo_res)
    return res
