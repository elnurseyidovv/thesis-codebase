import csv
from github import Github, GithubException


g = Github('')


projects = [
  ""
]

fieldnames = ['project', 'pr_number', 'title', 'body', 'created_at', 'merged_at', 'state', 'status']


for project in projects:
    filename = project.replace('/', '_') + '_prs.csv'
    print(f"processing - {project}")

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        try:
            repo = g.get_repo(project)
            pulls = repo.get_pulls(state='all')
            count = 0
            for pull in pulls:
                status = 'open' if pull.state == 'open' else ('merged' if pull.merged_at else 'closed')
                writer.writerow({
                    'project': project,
                    'pr_number': pull.number,
                    'title': pull.title,
                    'body': pull.body,
                    'created_at': pull.created_at.isoformat(),
                    'merged_at': pull.merged_at.isoformat() if pull.merged_at else None,
                    'state': pull.state,
                    'status': status
                })
                count += 1
            print(f"Fetched {count} PRs from {project} to {filename}")
        except GithubException as e:
                print(f"error - {project}")