import os
import requests
import re
import time
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Fetch GitHub repository information.')
parser.add_argument('parent_dir', help='Path to the parent directory containing repositories')
folder_path = ''

# Get GitHub token from environment variable
token = ''
if not token:
    raise ValueError("GITHUB_TOKEN environment variable not set")

# Set up headers for GitHub API requests
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

# List all subdirectories in the parent directory
project_folders = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]

# Process each subdirectory
for project_folder in project_folders:
    # Check for .git/config file
    git_config_path = os.path.join(folder_path, project_folder, '.git', 'config')
    if not os.path.exists(git_config_path):
        print(f"Skipping {project_folder}: no .git/config found")
        continue

    # Read .git/config to extract GitHub repository URL
    with open(git_config_path, 'r') as f:
        config_content = f.read()

    # Find GitHub repository URL (handles HTTPS and SSH formats)
    https_match = re.search(r"url = https://github\.com/([^/]+)/([^/\.]+)\.git", config_content)
    ssh_match = re.search(r"url = git@github\.com:([^/]+)/([^/]+)", config_content)

    if https_match:
        owner = https_match.group(1)
        repo = https_match.group(2)
    elif ssh_match:
        owner = ssh_match.group(1)
        repo = ssh_match.group(2)
        repo = repo.rstrip('.git')  # Remove .git if present in SSH URL
    else:
        print(f"Skipping {project_folder}: could not find GitHub repository URL in .git/config")
        continue

    repo_name = f"{owner}/{repo}"
    print(f"Processing project: {repo_name} from folder: {project_folder}")

    # Fetch repository details
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(repo_url, headers=headers)
    if response.status_code == 200:
        repo_data = response.json()
        repo_id = repo_data.get('id')
        stars = repo_data.get('stargazers_count')
        created_at = repo_data.get('created_at')
    else:
        print(f"Error fetching repository details for {repo_name}: {response.status_code}")
        continue

    # Fetch number of closed pull requests
    pr_url = f"https://api.github.com/search/issues?q=repo:{owner}/{repo}+type:pr+state:closed"
    response = requests.get(pr_url, headers=headers)
    if response.status_code == 200:
        pr_data = response.json()
        closed_prs = pr_data.get('total_count', 0)
    else:
        print(f"Error fetching closed PRs for {repo_name}: {response.status_code}")
        closed_prs = 0

    # Print the information
    print(f"Folder: {project_folder}")
    print(f"Project: {repo_name}")
    print(f"ID: {repo_id}")
    print(f"Stars: {stars}")
    print(f"Closed PRs: {closed_prs}")
    print(f"Created at: {created_at}")
    print()

    # Delay to respect rate limits
    time.sleep(1)