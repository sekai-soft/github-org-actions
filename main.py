import os
import datetime
import sentry_sdk
from typing import Annotated
from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings, SettingsConfigDict
from github_org_actions.models import RepoResult, Result
from github_org_actions.github import get_res


if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
    )


class Settings(BaseSettings):
    github_token: str
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
    "requested": "🕒",
    "queued": "🕒",
    "in_progress": "🔄",
    # "completed": "",  // This state should technically not be considered once there is a conclusion
    "waiting": "🕒",
    "pending": "🕒",
    # GitHub GQL CheckConclusionState
    "action_required": "🕒",
    "timed_out": "❌",
    "cancelled": "🟡",
    "failure": "❌",
    "success": "✅",
    "neutral": "🟡",
    "skipped": "🟡",
    "startup_failure": "❌",
    # "stale": "",  // The check suite or run was marked stale by GitHub. Only GitHub can use this conclusion.
}


def workflow_status_to_emoji(workflow_status: str) -> str:
    return workflow_status_to_emoji_map.get(workflow_status, "❓")


status_emoji_precedence = [
    "❌", "🕒", "🔄", "✅", "🟡"
]


def repo_status_emoji(repo_res: RepoResult) -> str:
    res = status_emoji_precedence[-1]
    for workflow in repo_res.workflows:
        emoji = workflow_status_to_emoji(workflow.status)
        if emoji in status_emoji_precedence \
            and status_emoji_precedence.index(emoji) < status_emoji_precedence.index(res):
            res = emoji
    return res


@app.get("/api/{org}")
async def _api(org: str, e: Annotated[list[str], Query(title="Excluded repos")] = []) -> list[RepoResult]:
    return await get_res(org, e, settings.github_token)


@app.get("/")
async def _root(
    request: Request,
    o: Annotated[str, Query(title="GitHub Org")] = None,
    e: Annotated[list[str], Query(title="Excluded repos")] = [],
    dar: Annotated[bool, Query(title="Disable auto-refresh")] = False
):
    if not o:
        return templates.TemplateResponse(
            request=request,
            name="index.html"
        )

    res = await get_res(o, e, settings.github_token)
    if not res:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": f"GitHub org '{o}' not found"}
        )

    return templates.TemplateResponse(
        request=request,
        name="org.html",
        context={
            "res": res,
            "auto_refresh": not dar,
            "time_ago": time_ago,
            "workflow_status_to_emoji": workflow_status_to_emoji,
            "repo_status_emoji": repo_status_emoji
        }
    )
