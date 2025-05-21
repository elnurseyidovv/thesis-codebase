import requests
from collections import Counter
import time


def get_domain(email):
    if email and '@' in email:
        domain = email.split('@')[1].lower()
        if domain == 'users.noreply.github.com':
            return None
        return domain
    return None


try:
    with open('../community_potential_projects.txt', 'r') as f:
        repos = [line.strip() for line in f if line.strip()]
except Exception as e:
    print(f"Error reading")
    exit(0)

headers = {'Authorization': f'token ', 'Accept': 'application/vnd.github.v3+json'}

list5 = []

for i, repo_n in enumerate(repos, 1):
    owner, repo_name = repo_n.split('/')

    contrib_url = f'https://api.github.com/repos/{owner}/{repo_name}/contributors?per_page=20'
    response = requests.get(contrib_url, headers=headers)
    if response.status_code == 200:
        contributors = response.json()[:20]
    else:
        print(f"error contributors fetch - {repo_n}")
        continue

    emails = []
    for contrib in contributors:
        login = contrib.get('login')
        commit_url = f'https://api.github.com/repos/{owner}/{repo_name}/commits?author={login}&per_page=1'
        response = requests.get(commit_url, headers=headers)
        commits = response.json()
        if commits:
            email = commits[0]['commit']['author'].get('email')
            emails.append(email)

    domains = [get_domain(email) for email in emails if get_domain(email)]

    if domains:
        counter = Counter(domains)
        max_freq = counter.most_common(1)[0][1]
    else:
        max_freq = 0

    if max_freq <= 5:
        list5.append(repo_n)

    time.sleep(1)

print("\nfound projects:")
if list5:
    for repo in list5:
        print(f"- {repo}")
else:
    print("None")