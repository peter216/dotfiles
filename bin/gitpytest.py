import os

import git

# Set up repository path and GitHub credentials
repo_path = "~/bin"
github_token = os.getenv("GHTOKEN")
remote_name = "origin"
branch_name = "development"

# Initialize the repository
repo = git.Repo(repo_path)

# Create a file
os.system("touch testfile.txt")

# Stage changes
repo.git.add(update=True)

# Commit changes
commit_message = "foo.txt has been added"
repo.index.commit(commit_message)

# Set up remote with authentication
remote_url = f"https://{github_token}@git.marriott.com/prube194/bin.git"
# repo.create_remote(remote_name, remote_url)

# Push changes
repo.git.push(remote_name, branch_name)

print("Changes have been pushed to GitHub.")
