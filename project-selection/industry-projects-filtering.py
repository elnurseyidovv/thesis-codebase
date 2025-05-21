import os
import requests
import json
import time
import pandas as pd

headers = {'Authorization': f'token ', 'Accept': 'application/vnd.github.v3+json'}


df = pd.read_csv('../Industry-Backed-Attempts.csv', delimiter=';')

for index, row in df.iterrows():
    project = row['Projects']
    email_domain = row['Email Domain'].lower()
    owner, repo = project.split('/')
    repo_full_name = f"{owner}/{repo}"

    print(f"processing {repo_full_name}")

    contrib_url = f'https://api.github.com/repos/{repo_full_name}/contributors?per_page=20'
    response = requests.get(contrib_url, headers=headers)
    if response.status_code == 200:
        contributors = response.json()[:20]
    else:
        print(f"error contributors fetch - {repo_full_name}")
        continue

    authors = []
    matching_count = 0
    for contrib in contributors:
        login = contrib.get('login')
        commits = contrib.get('contributions', 0)

        commit_url = f'https://api.github.com/repos/{repo_full_name}/commits?author={login}&per_page=1'
        try:
            response = requests.get(commit_url, headers=headers)
            if response.status_code == 200 and len(response.json()) > 0:
                commit = response.json()[0]
                email = commit['commit']['author'].get('email', None)
                if email and '@' in email:
                    domain = email.split('@')[-1].lower()
                    matching = domain == email_domain
                    if matching:
                        matching_count += 1
                else:
                    matching = False
                    email = None
            else:
                matching = False
                email = None
        except Exception as e:
            print(f"Error fetching commit for {login} in {repo_full_name}: {e}")
            matching = False
            email = None

        authors.append({
            'login': login,
            'email': email,
            'commits': commits
        })

    if matching_count > 10:
        project_data = {
            'project_url': f'https://github.com/{repo_full_name}',
            'top_authors': authors
        }
        print(json.dumps(project_data, indent=2))

    time.sleep(2)