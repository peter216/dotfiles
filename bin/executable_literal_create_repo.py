#!/usr/bin/env python
import os
import subprocess
import sys

import urllib3
from github import Github

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_github_repo(repo_name, token):
    g = Github(token, verify=False)
    org = g.get_organization("Network-DevOps")
    repo = org.create_repo(name=repo_name, private=True, visibility="internal")
    print(f"Repository '{repo_name}' created successfully.")
    return repo


def set_team_permissions(repo, token):
    g = Github(token, verify=False)
    org = g.get_organization("Network-DevOps")
    team = org.get_team_by_slug("network-devops")
    team.add_to_repos(repo)
    team.update_team_repository(repo, "maintain")
    print(f"Permissions set successfully for team 'network-devops'.")


def set_admin_permissions(repo, token):
    g = Github(token, verify=False)
    user = g.get_user(os.getenv("GITHUB_USER"))
    repo.add_to_collaborators(user.login, "admin")
    print(f"Admin permissions set successfully for user '{user.login}'.")


def create_local_repo(repo_name):
    repo_path = os.path.join(os.getcwd(), repo_name)
    os.makedirs(repo_path)
    with open(os.path.join(repo_path, "README.md"), "w") as f:
        f.write(
            f"# {repo_name}\n\nThis is the README file for the {repo_name} repository."
        )
    repo = git.Repo.init(repo_path)
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    origin = repo.create_remote(
        "origin", f"https://git.marriott.com/Network-DevOps/{repo_name}.git"
    )
    repo.git.push("origin", "master", set_upstream=True)


def main():
    if len(sys.argv) != 2:
        print("Usage: python create_repo.py <repo_name>")
        sys.exit(1)

    repo_name = sys.argv[1]
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        sys.exit(1)

    try:
        repo = create_github_repo(repo_name, token)
        set_team_permissions(repo, token)
        set_admin_permissions(repo, token)
        create_local_repo(repo_name)
    except Exception as e:
        print(f"Error: {e.__class__.__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
