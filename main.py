import os
import datetime
import sentry_sdk
from typing import Annotated
from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings, SettingsConfigDict
from github_org_actions.models import RepoResult
from github_org_actions.github import get_res


if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
    )


class Settings(BaseSettings):
    github_token: str
    ui_default_org: str
    ui_default_excluded_repos: str
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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


workflow_status_to_emoji_map = {
    # GitHub GQL CheckStatusState
    "requested": "🔄",
    "queued": "🕒",
    "in_progress": "🔄",
    "completed": "🏁",
    "waiting": "⏳",
    "pending": "⏳",
    # GitHub GQL CheckConclusionState
    "action_required": "✋",
    "timed_out": "⏰",
    "cancelled": "🚫",
    "failure": "❌",
    "success": "✅",
    "neutral": "🟡",
    "skipped": "⏭️",
    "startup_failure": "🚫",
    # "stale": "",  // The check suite or run was marked stale by GitHub. Only GitHub can use this conclusion.
}


def workflow_status_to_emoji(workflow_status: str) -> str:
    return workflow_status_to_emoji_map.get(workflow_status, "❓")


@app.get("/")
async def _root(request: Request):
    res = await get_res(settings.ui_default_org, settings.ui_default_excluded_repos.split(","), settings.github_token)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "res": res,
            "time_ago": time_ago,
            "workflow_status_to_emoji": workflow_status_to_emoji
        }
    )


@app.get("/api/{org}")
async def _api(org: str, e: Annotated[list[str], Query()] = []) -> list[RepoResult]:
    return await get_res(org, e, settings.github_token)
