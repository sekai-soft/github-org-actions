from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportQueryError
from .models import WorkflowResult, RepoResult, Result


async def call_gql(query, variables, token):
    headers = {"Authorization": f"Bearer {token}"}
    transport = AIOHTTPTransport(url="https://api.github.com/graphql", headers=headers)
    client = Client(transport=transport)
    return await client.execute_async(gql(query), variable_values=variables)


GET_RES_GQL = """
query GitHubOrgActions($org: String!) {
  organization(login: $org) {
    name
    repositories(visibility: PUBLIC, isArchived: false, first: 100) {
      nodes {
        name
        url
        defaultBranchRef {
          target {
            abbreviatedOid
            commitUrl
            ... on Commit {
              checkSuites(first: 100, filterBy: {appId: 15368}) {
                nodes {
                  status
                  conclusion
                  workflowRun {
                    createdAt
                    url
                    workflow {
                      name
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


async def get_res(org: str, excluded_repos: list[str], token: str) -> Result | None:
    try:
      gql_res = await call_gql(GET_RES_GQL, {"org": org}, token)
    except TransportQueryError:
      return None
    
    repo_results = []
    for repo in gql_res["organization"]["repositories"]["nodes"]:
        if repo["name"] in excluded_repos:
            continue
        
        if not repo["defaultBranchRef"] \
            or not repo["defaultBranchRef"]["target"] \
                or not repo["defaultBranchRef"]["target"]["checkSuites"] \
                    or not repo["defaultBranchRef"]["target"]["checkSuites"]["nodes"]:
            continue
       
        workflow_res_list = []  # type: list[WorkflowResult]
        for check_suite in repo["defaultBranchRef"]["target"]["checkSuites"]["nodes"]:
            if not check_suite["workflowRun"]:
                continue
            workflow_res_list.append(WorkflowResult(
                name=check_suite["workflowRun"]["workflow"]["name"],
                run_url=check_suite["workflowRun"]["url"],
                created_at=check_suite["workflowRun"]["createdAt"],
                status=(check_suite["conclusion"] or check_suite["status"]).lower()
            ))
        workflow_res_list.sort(key=lambda x: x.created_at, reverse=True)
        if not workflow_res_list:
            continue

        repo_results.append(RepoResult(
            name=repo["name"],
            repo_url=repo["url"],
            latest_commit=repo["defaultBranchRef"]["target"]["abbreviatedOid"],
            latest_commit_url=repo["defaultBranchRef"]["target"]["commitUrl"],
            workflows=workflow_res_list
        ))
    repo_results.sort(key=lambda x: min([w.created_at for w in x.workflows]), reverse=True)

    return Result(
      org_name=gql_res["organization"]["name"],
      repos=repo_results
    )
