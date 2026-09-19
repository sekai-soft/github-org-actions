from datetime import datetime, timezone
from pydantic import BaseModel, computed_field


WORKFLOW_STATUS_TO_EMOJI_MAP = {
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


STATUS_EMOJI_PRECEDENCE = [
    "❌", "🕒", "🔄", "✅", "🟡"
]


def format_time_ago(timestamp: datetime) -> str:
    now = datetime.now(timezone.utc)
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


class WorkflowResult(BaseModel):
    name: str
    run_url: str
    created_at: datetime
    status: str

    @computed_field
    @property
    def status_emoji(self) -> str:
        return WORKFLOW_STATUS_TO_EMOJI_MAP.get(self.status, "❓")

    @computed_field
    @property
    def time_ago(self) -> str:
        return format_time_ago(self.created_at)


class RepoResult(BaseModel):
    name: str
    repo_url: str
    latest_commit: str
    latest_commit_url: str
    workflows: list[WorkflowResult]

    @computed_field
    @property
    def status_emoji(self) -> str:
        res = STATUS_EMOJI_PRECEDENCE[-1]
        for workflow in self.workflows:
            emoji = workflow.status_emoji
            if emoji in STATUS_EMOJI_PRECEDENCE \
                and STATUS_EMOJI_PRECEDENCE.index(emoji) < STATUS_EMOJI_PRECEDENCE.index(res):
                res = emoji
        return res


class Result(BaseModel):
    org_name: str
    repos: list[RepoResult]
