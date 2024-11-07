import datetime
from typing import Annotated
from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings, SettingsConfigDict
from github import Github, Auth
from github_org_actions.models import RepoResult
from github_org_actions.github import get_repo_res


class Settings(BaseSettings):
    github_token: str
    ui_default_org: str
    ui_default_excluded_repos: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
app = FastAPI()
templates = Jinja2Templates(directory="templates")
auth = Auth.Token(settings.github_token)
github = Github(auth=auth)


def _get_res(org: str, excluded_repos: list[str]) -> list[RepoResult]:
    org = github.get_organization(org)
    repos = org.get_repos(type="public")

    res = []
    for repo in repos:
        repo_res = get_repo_res(repo, excluded_repos)
        if repo_res:
            res.append(repo_res)
    res.sort(key=lambda x: min([w.created_at for w in x.workflows]), reverse=True)

    return res


def time_ago(timestamp):
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - timestamp
    seconds = diff.total_seconds()
    
    if seconds >= 31536000:
        return f"{int(seconds // 31536000)}y ago"
    elif seconds >= 2592000:
        return f"{int(seconds // 2592000)}mo ago"
    elif seconds >= 86400:
        return f"{int(seconds // 86400)}d ago"
    elif seconds >= 3600:
        return f"{int(seconds // 3600)}h ago"
    elif seconds >= 60:
        return f"{int(seconds // 60)}m ago"
    else:
        return f"{int(seconds)}s ago"


@app.get("/")
async def _root(request: Request):
    res = _get_res(settings.ui_default_org, settings.ui_default_excluded_repos.split(","))
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"res": res, "time_ago": time_ago}
    )


@app.get("/api/{org}")
async def _api(org: str, e: Annotated[list[str], Query()] = []) -> list[RepoResult]:
    return _get_res(org, e)
