from github.Repository import Repository
from github.Branch import Branch
from github.Workflow import Workflow
from github.WorkflowRun import WorkflowRun
from .models import WorkflowResult, RepoResult


def try_get_master_branch(repo: Repository) -> Branch | None:
    try:
        return repo.get_branch("main")
    except:
        try:
            return repo.get_branch("master")
        except:
            return None


def get_workflow_res(workflow: Workflow, head_sha: str) -> WorkflowResult | None:
    runs = workflow.get_runs(head_sha=head_sha).get_page(0)
    if not runs:
        return None
    run = runs[0]  # type: WorkflowRun
    return WorkflowResult(
        name=workflow.name,
        created_at=run.created_at,
        status=run.status
    )


def get_repo_res(repo: Repository, excluded_repo: list[str]) -> RepoResult | None:
    if repo.name in excluded_repo:
        return None
    
    if repo.archived:
        return None

    master_branch = try_get_master_branch(repo)
    if not master_branch:
        return None
    head_sha = master_branch.commit.sha
    
    workflows = repo.get_workflows()
    if workflows.totalCount == 0:
        return None

    workflow_res_list = []  # type: list[WorkflowResult]
    for workflow in workflows:
        workflow_res = get_workflow_res(workflow, head_sha)
        if workflow_res:
            workflow_res_list.append(workflow_res)
    workflow_res_list.sort(key=lambda x: x.created_at, reverse=True)

    return RepoResult(
        name=repo.name,
        workflows=workflow_res_list
    )
