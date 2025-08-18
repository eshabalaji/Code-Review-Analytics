import os
import requests
import base64
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from collections import defaultdict

# ===== CONFIG =====
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or input("Enter your GitHub Token: ").strip()
OWNER = os.getenv("OWNER") or input("Enter repo owner: ").strip()
REPO = os.getenv("REPO") or input("Enter repo name: ").strip()

os.environ['GITHUB_TOKEN'] = GITHUB_TOKEN
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}
BASE_URL = f'https://api.github.com/repos/{OWNER}/{REPO}'



# ========== FETCH FUNCTIONS ==========

def fetch_repo_data():
    url = BASE_URL
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching repo data:", response.json())
        return None


def fetch_commits():
    url = f"{BASE_URL}/commits"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []


def fetch_contributors():
    url = f"{BASE_URL}/contributors"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []


def fetch_pull_requests_with_details():
    pr_url = f"{BASE_URL}/pulls?state=all"
    response = requests.get(pr_url, headers=HEADERS)
    pr_data = []

    if response.status_code == 200:
        pulls = response.json()
        for pr in pulls:
            pr_number = pr["number"]
            pr_title = pr["title"]
            pr_user = pr["user"]["login"]
            pr_state = pr["state"]
            pr_created = pr["created_at"]

            # Fetch reviewers
            reviewers_url = f"{BASE_URL}/pulls/{pr_number}/reviews"
            reviewers_resp = requests.get(reviewers_url, headers=HEADERS)
            reviewers = [r["user"]["login"] for r in reviewers_resp.json()] if reviewers_resp.status_code == 200 else []

            # Fetch comments
            comments_url = f"{BASE_URL}/issues/{pr_number}/comments"
            comments_resp = requests.get(comments_url, headers=HEADERS)
            commenters = [c["user"]["login"] for c in comments_resp.json()] if comments_resp.status_code == 200 else []

            pr_data.append({
                "number": pr_number,
                "title": pr_title,
                "author": pr_user,
                "state": pr_state,
                "created_at": pr_created,
                "reviewers": reviewers,
                "commenters": commenters
            })
    else:
        print("Error fetching PRs:", response.json())

    return pr_data


def fetch_issues():
    url = f"{BASE_URL}/issues?state=all"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []


# ========== DATA PROCESSING ==========

def group_commits_by_date_and_author(commits):
    date_count = defaultdict(int)
    author_count = defaultdict(int)
    for commit in commits:
        date_str = commit["commit"]["author"]["date"][:10]
        author = commit["commit"]["author"]["name"]
        date_count[date_str] += 1
        author_count[author] += 1
    return date_count, author_count


def issues_fixed_by(issues):
    fixed_map = defaultdict(list)
    for issue in issues:
        if issue.get("state") == "closed" and "pull_request" in issue:
            fixed_map[issue["user"]["login"]].append(issue["number"])
    return fixed_map


# ========== SAVE HELPERS ==========

def save_contributors_csv(contributors, filename="contributors.csv"):
    df = pd.DataFrame(contributors)
    df.to_csv(filename, index=False)
    print(f"✅ Saved contributors to {filename}")


def save_prs_csv(pr_data, filename="pull_requests.csv"):
    df = pd.DataFrame(pr_data)
    df.to_csv(filename, index=False)
    print(f"✅ Saved PR data to {filename}")


def save_issues_csv(issues, filename="issues.csv"):
    df = pd.DataFrame(issues)
    df.to_csv(filename, index=False)
    print(f"✅ Saved issues to {filename}")


# ========== PLOTS ==========

def plot_commit_activity(date_count):
    dates = sorted(date_count.keys())
    counts = [date_count[d] for d in dates]
    plt.figure()
    plt.plot(dates, counts, marker="o")
    plt.xticks(rotation=45)
    plt.title("Commits per Day")
    plt.xlabel("Date")
    plt.ylabel("Commits")
    plt.tight_layout()
    plt.show()


def plot_author_activity(author_count):
    authors = list(author_count.keys())
    counts = list(author_count.values())
    plt.figure()
    plt.bar(authors, counts)
    plt.xticks(rotation=45)
    plt.title("Commits per Author")
    plt.xlabel("Author")
    plt.ylabel("Commits")
    plt.tight_layout()
    plt.show()


def plot_pr_timeline(pr_data):
    dates = [pr["created_at"][:10] for pr in pr_data]
    counts = defaultdict(int)
    for d in dates:
        counts[d] += 1
    sorted_dates = sorted(counts.keys())
    values = [counts[d] for d in sorted_dates]
    plt.figure()
    plt.plot(sorted_dates, values, marker="o")
    plt.xticks(rotation=45)
    plt.title("PR Timeline")
    plt.xlabel("Date")
    plt.ylabel("Number of PRs")
    plt.tight_layout()
    plt.show()


def plot_open_vs_closed_issues_counts(issues):
    open_count = sum(1 for i in issues if i["state"] == "open")
    closed_count = sum(1 for i in issues if i["state"] == "closed")
    plt.figure()
    plt.bar(["Open", "Closed"], [open_count, closed_count])
    plt.title("Issues: Open vs Closed")
    plt.tight_layout()
    plt.show()


def plot_issues_fixed_by(fixed_map):
    authors = list(fixed_map.keys())
    counts = [len(v) for v in fixed_map.values()]
    plt.figure()
    plt.bar(authors, counts)
    plt.xticks(rotation=45)
    plt.title("Issues Fixed by Contributors")
    plt.xlabel("Contributor")
    plt.ylabel("Issues Fixed")
    plt.tight_layout()
    plt.show()


def plot_pr_comment_activity(pr_data):
    """Plot number of PR comments per user (reviewers + commenters)."""
    user_comment_count = defaultdict(int)
    for pr in pr_data:
        for user in pr["reviewers"]:
            user_comment_count[user] += 1
        for user in pr["commenters"]:
            user_comment_count[user] += 1

    if not user_comment_count:
        print("⚠️ No PR comments/reviews found.")
        return

    users = list(user_comment_count.keys())
    counts = list(user_comment_count.values())

    plt.figure()
    plt.bar(users, counts)
    plt.xticks(rotation=45)
    plt.title("PR Comments/Reviews per User")
    plt.xlabel("User")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.show()


# ========== MAIN ==========

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

    commits = fetch_commits()
    date_count, author_count = group_commits_by_date_and_author(commits)

    contributors = fetch_contributors()
    print(f"Total Contributors: {len(contributors)}")

    pr_data = fetch_pull_requests_with_details()
    issues = fetch_issues()
    fixed_map = issues_fixed_by(issues)

    # Display PR table with reviewers + commenters
    pr_df = pd.DataFrame(pr_data)
    print("\nPull Request Data (with Reviewers & Commenters):\n", 
          pr_df[['number','title','author','reviewers','commenters']])

    # Save to CSV
    save_contributors_csv(contributors)
    save_prs_csv(pr_data)
    save_issues_csv(issues)

    # Plots
    plot_commit_activity(date_count)
    plot_author_activity(author_count)
    plot_pr_timeline(pr_data)
    plot_open_vs_closed_issues_counts(issues)
    plot_issues_fixed_by(fixed_map)
    plot_pr_comment_activity(pr_data)


if __name__ == "__main__":
    main()
