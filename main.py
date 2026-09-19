import os
import sentry_sdk
from typing import Annotated
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings, SettingsConfigDict
from github_org_actions.models import Result
from github_org_actions.github import GetResError, get_res


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

    try:
        res = await get_res(o, e, settings.github_token)
    except GetResError as err:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": str(err)}
        )

    return templates.TemplateResponse(
        request=request,
        name="org.html",
        context={
            "res": res,
            "auto_refresh": not dar
        }
    )


@app.get("/api")
async def _api(
    o: Annotated[str, Query(title="GitHub Org")],
    e: Annotated[list[str], Query(title="Excluded repos")] = []
) -> Result:
    try:
        return await get_res(o, e, settings.github_token)
    except GetResError as err:
        raise HTTPException(status_code=400, detail=str(err))
