import requests
import csv
import time
from urllib.parse import urlparse

enterprise_repos = set()
try:
    with open("enterprise_projects.txt", "r") as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if row:
                url = row[0].strip()
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                owner, repo = path_parts
                enterprise_repos.add(f"{owner}/{repo}")
except FileNotFoundError:
    print("list not found")
    exit(1)


headers = {"Authorization": f"token ", "Accept": "application/vnd.github.v3+json"}
params = {
    "q": "language:Java stars:>500 created:<2018-04-30 pushed:>2025-01-30",
    "sort": "stars",
    "order": "desc",
    "per_page": 100,
    "page": 1
}

candidates = []
while params["page"] <= 20:
    print(f"page: {params["page"]}")
    response = requests.get("https://api.github.com/search/repositories", headers=headers, params=params)
    data = response.json()
    for repo in data["items"]:
        full_name = repo["full_name"]
        if full_name in enterprise_repos:
            print(f"{full_name} found in enterprise list")
        else:
            candidates.append(full_name)
            logger.info(f"added candidate - {full_name}")
    if "next" not in response.links or params["page"] == 20:
        break
    params["page"] += 1
    time.sleep(2)

print(f"candidates before PR check - {len(candidates)}")

final_candidates = []
max_final_candidates = 100

for repo in candidates:
    if len(final_candidates) >= max_final_candidates:
        print("found enough candidates")
        break

    params = {
        "q": f"repo:{repo} type:pr",
        "per_page": 1
    }
    response = requests.get("https://api.github.com/search/issues", headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        total_prs = data.get("total_count", 0)
        if total_prs > 1950:
            final_candidates.append(repo)
    else:
        print(f"error fetching PRs - {repo}")
    time.sleep(2)


print("repositories found:")
for repo in final_candidates:
    print(f"https://github.com/{repo}")