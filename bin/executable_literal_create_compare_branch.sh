#!/bin/bash

# Get the current branch name
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Check if already on a compare branch to avoid infinite loops
if [[ $current_branch == *"-compare" ]]; then
    echo "Already on a compare branch. Skipping creation."
    exit 0
fi

# Define the compare branch name
compare_branch="${current_branch}-compare"

# Check if the compare branch already exists
if git show-ref --verify --quiet "refs/heads/$compare_branch"; then
    echo "Compare branch $compare_branch already exists. Deleting and recreating it."
    git branch -D "$compare_branch"
else
    echo "Creating compare branch: $compare_branch"
fi

# Create a fresh compare branch based on the current branch
git branch "$compare_branch"

# Print success message
echo "Compare branch $compare_branch created successfully as a fresh copy of $current_branch."
