import requests
import base64
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from collections import defaultdict
from datetime import datetime
import os

# ==== 🔐 Configuration ==== 

GITHUB_TOKEN = input("Enter your GitHub Personal Access Token: ").strip()
OWNER = input("Enter the repository owner username: ").strip()
REPO = input("Enter the repository name: ").strip()

os.environ['GITHUB_TOKEN'] = GITHUB_TOKEN
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}
BASE_URL = f'https://api.github.com/repos/{OWNER}/{REPO}'

# ==== 🔁 Utilities ====
def get_paginated_data(url):
    results = []
    while url:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            break
        results += res.json()
        url = res.links['next']['url'] if 'next' in res.links else None
    return results

# ==== 📦 Repo Info ====
def fetch_repo_data():
    res = requests.get(BASE_URL, headers=HEADERS)
    if res.status_code == 200:
        data = res.json()
        print("Repository Name:", data['name'])
        print("Description:", data['description'])
        print("Stars:", data['stargazers_count'])
        print("Forks:", data['forks_count'])
        print("Open Issues:", data['open_issues_count'])
        print("Created at:", data['created_at'])
        print("Last updated:", data['updated_at'])
        return data
    else:
        print("Failed to fetch repo data:", res.status_code)
        return None

# ==== 📖 README ====
def fetch_readme():
    url = f'{BASE_URL}/readme'
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        content = base64.b64decode(res.json()['content']).decode('utf-8')
        print("\nREADME Content:\n")
        print(content)
    else:
        print("Failed to fetch README:", res.status_code)

# ==== 🚀 Commits ====
def fetch_commits():
    return get_paginated_data(f'{BASE_URL}/commits')

def group_commits_by_date_and_author(commits):
    date_count = defaultdict(int)
    author_count = defaultdict(int)
    for commit in commits:
        date = datetime.strptime(commit['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ").date()
        author = commit['commit']['author']['name']
        date_count[date] += 1
        author_count[author] += 1
    return date_count, author_count

# ==== 👥 Contributors ====
def fetch_contributors():
    return get_paginated_data(f'{BASE_URL}/contributors')

# ==== 🔃 Pull Requests ====
def fetch_pull_requests():
    return get_paginated_data(f'{BASE_URL}/pulls?state=all')

def print_pull_requests(prs):
    if not prs:
        print("0 pull requests")
    else:
        for pr in prs:
            print(f"PR #{pr['number']} by {pr['user']['login']}: {pr['title']} (State: {pr['state']})")

# ==== 📁 File Tree Download ====
def download_all_files(repo_data):
    branch = repo_data['default_branch']
    tree_url = f'{BASE_URL}/git/trees/{branch}?recursive=1'
    res = requests.get(tree_url, headers=HEADERS)
    tree = res.json().get('tree', [])
    blobs = [f for f in tree if f['type'] == 'blob']
    print(f"Total files found: {len(blobs)}")

    for file in blobs:
        raw_url = f'https://raw.githubusercontent.com/{OWNER}/{REPO}/{branch}/{file["path"]}'
        content = requests.get(raw_url).text
        print(f"Downloading: {file['path']}")
        with open(file['path'], 'w', encoding='utf-8') as f:
            f.write(content)

# ==== 📊 Visualizations ====
def plot_commit_activity(date_count):
    df = pd.DataFrame(sorted(date_count.items()), columns=['Date', 'Commits'])
    plt.figure(figsize=(6, 5))
    sns.lineplot(data=df, x='Date', y='Commits', marker='o')
    plt.title('Commits per Day')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_author_activity(author_count):
    df = pd.DataFrame(author_count.items(), columns=['Author', 'CommitCount']).sort_values(by='CommitCount', ascending=False)
    plt.figure(figsize=(6, 5))
    sns.barplot(data=df, x='Author', y='CommitCount')
    plt.title('Commits per Contributor')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# ==== 🔁 Main ====
def main():
    repo_data = fetch_repo_data()
    if not repo_data:
        return

    fetch_readme()

    # Commits
    commits = fetch_commits()
    print(f"Total commits: {len(commits)}")
    date_count, author_count = group_commits_by_date_and_author(commits)

    # Pull Requests
    prs = fetch_pull_requests()
    print_pull_requests(prs)

    # Contributors (optional usage)
    contributors = fetch_contributors()
    print(f"\nTotal Contributors: {len(contributors)}")

    # Files (optional - uncomment to download files)
    # download_all_files(repo_data)

    # Visualizations
    plot_commit_activity(date_count)
    plot_author_activity(author_count)

# Run the script
if __name__ == "__main__":
    main()
