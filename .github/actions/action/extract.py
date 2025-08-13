import os
import requests
import base64
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from collections import defaultdict

# ==== CONFIG ====
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or input("Enter your GitHub Token: ").strip()
OWNER = os.getenv("OWNER") or input("Enter repo owner: ").strip()
REPO = os.getenv("REPO") or input("Enter repo name: ").strip()

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
        return res.json()
    else:
        print("Failed to fetch repo data:", res.status_code)
        return None

# ==== 📖 README ====
'''def fetch_readme():
    url = f'{BASE_URL}/readme'
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        content = base64.b64decode(res.json()['content']).decode('utf-8')
        print("\nREADME Content:\n", content)
    else:
        print("Failed to fetch README:", res.status_code)

'''

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

# Detailed PR Data
def fetch_pull_requests_with_details():
    prs = get_paginated_data(f'{BASE_URL}/pulls?state=all')
    pr_data = []
    for pr in prs:
        pr_number = pr['number']
        pr_details_url = f'{BASE_URL}/pulls/{pr_number}'
        pr_details = requests.get(pr_details_url, headers=HEADERS).json()

        reviews_url = f'{BASE_URL}/pulls/{pr_number}/reviews'
        reviews = get_paginated_data(reviews_url)
        reviewers = list(set(r['user']['login'] for r in reviews if r.get('user')))

        comments_url = f'{BASE_URL}/issues/{pr_number}/comments'
        comments = get_paginated_data(comments_url)
        commenters = list(set(c['user']['login'] for c in comments if c.get('user')))

        pr_data.append({
            'number': pr_number,
            'title': pr['title'],
            'author': pr['user']['login'],
            'state': pr['state'],
            'created_at': pr['created_at'],
            'merged_at': pr.get('merged_at'),
            'reviewers': reviewers,
            'commenters': commenters
        })
    return pr_data

# ==== 🐞 Issues ====
def fetch_issues():
    return get_paginated_data(f'{BASE_URL}/issues?state=all')

def issues_fixed_by(issues):
    fixed_map = defaultdict(int)
    for issue in issues:
        if issue.get('state') == 'closed' and issue.get('closed_by'):
            fixed_map[issue['closed_by']['login']] += 1
    return fixed_map

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

def plot_pr_timeline(pr_data):
    df = pd.DataFrame(pr_data)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df_open = df[df['state'] == 'open']
    df_closed = df[df['state'] == 'closed']

    plt.figure(figsize=(7, 5))
    plt.hist(df_open['created_at'], bins=10, alpha=0.7, label='Open PRs')
    plt.hist(df_closed['created_at'], bins=10, alpha=0.7, label='Closed PRs')
    plt.legend()
    plt.title('PRs Created Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of PRs')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_open_vs_closed_issues_counts(issues):
    open_count = sum(1 for i in issues if i['state'] == 'open')
    closed_count = sum(1 for i in issues if i['state'] == 'closed')

    plt.figure(figsize=(6, 5))
    plt.bar(['Open', 'Closed'], [open_count, closed_count], color=['skyblue', 'lightgreen'])
    plt.title('Open vs Closed Issues (Count)')
    plt.ylabel('Number of Issues')

    # Annotate counts above bars
    for idx, count in enumerate([open_count, closed_count]):
        plt.text(idx, count + 0.5, str(count), ha='center', fontsize=12)

    plt.show()


def plot_issues_fixed_by(fixed_map):
    df = pd.DataFrame(fixed_map.items(), columns=['User', 'Issues Fixed']).sort_values(by='Issues Fixed', ascending=False)
    plt.figure(figsize=(6, 5))
    sns.barplot(data=df, x='User', y='Issues Fixed')
    plt.title('Issues Fixed by Contributor')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# ==== Main ====
def main():
    repo_data = fetch_repo_data()
    if not repo_data:
        return
    
    print(f"Repository: {repo_data['name']}")
    print(f"Description: {repo_data['description']}")
    print(f"Stars: {repo_data['stargazers_count']}, Forks: {repo_data['forks_count']}")
    print(f"Open Issues: {repo_data['open_issues_count']}")
    created = datetime.strptime(repo_data['created_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    updated = datetime.strptime(repo_data['updated_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    print(f"Created: {created}, Updated: {updated}")


    #fetch_readme()

    commits = fetch_commits()
    date_count, author_count = group_commits_by_date_and_author(commits)

    contributors = fetch_contributors()
    print(f"Total Contributors: {len(contributors)}")

    pr_data = fetch_pull_requests_with_details()
    issues = fetch_issues()
    fixed_map = issues_fixed_by(issues)

    # Table View of PRs
    pr_df = pd.DataFrame(pr_data)
    print("\nPull Request Data:\n", pr_df)

    # Plots
    plot_commit_activity(date_count)
    plot_author_activity(author_count)
    plot_pr_timeline(pr_data)
    plot_open_vs_closed_issues_counts(issues)
    plot_issues_fixed_by(fixed_map)

if __name__ == "__main__":
    main()
