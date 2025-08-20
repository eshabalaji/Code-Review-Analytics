import os
import sys
import requests
import pandas as pd
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

# ===== HTTP helpers =====
def _log_http_error(resp, where=""):
    try:
        err = resp.json()
    except (ValueError):
        err = {"message": resp.text}
    print(f"HTTP {resp.status_code} while {where} -> {err}", file=sys.stderr)

def get_paginated_data(url, params=None, where="GET (paginated)"):
    """Restore/ensure full pagination so we never stop at page 1."""
    params = params or {}
    params.setdefault("per_page", 100)
    results, page = [], 1
    while True:
        q = dict(params)
        q["page"] = page
        resp = requests.get(url, headers=HEADERS, params=q)
        if resp.status_code != 200:
            _log_http_error(resp, where=f"{where} {url}?page={page}")
            break
        try:
            batch = resp.json()
        except Exception:
            print(f"Failed to parse JSON page {page} at {url}", file=sys.stderr)
            break
        if not isinstance(batch, list) or not batch:
            break
        results += batch
        page += 1
        # stop when a short page arrives (no Link header required)
        if len(batch) < params["per_page"]:
            break
    return results

# ===== Repo info =====
def fetch_repo_data():
    res = requests.get(BASE_URL, headers=HEADERS)
    if res.status_code == 200:
        return res.json()
    else:
        _log_http_error(res, where="repo")
        return None

# ===== Commits =====
def fetch_commits():
    return get_paginated_data(f'{BASE_URL}/commits', where="commits")

def group_commits_by_date_and_author(commits):
    date_count = defaultdict(int)
    author_count = defaultdict(int)
    for commit in commits:
        try:
            date = datetime.strptime(commit['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ").date()
            author = commit['commit']['author']['name'] or "Unknown"
            date_count[date] += 1
            author_count[author] += 1
        except (KeyError, ValueError, TypeError) as e:
            print(f"Skipping malformed commit entry: {e}", file=sys.stderr)
    return date_count, author_count

# ===== Contributors =====
def fetch_contributors():
    return get_paginated_data(f'{BASE_URL}/contributors', where="contributors")

# ===== Pull Requests (detailed) =====
def _process_reviews(pr_number, author):
    reviews = get_paginated_data(f"{BASE_URL}/pulls/{pr_number}/reviews", where=f"reviews #{pr_number}") or []
    events, interactions, users = [], [], []
    for r in reviews:
        r_user = (r.get("user") or {}).get("login")
        r_state = r.get("state")
        r_time = r.get("submitted_at")
        events.append({"pr": pr_number, "reviewer": r_user, "state": r_state, "submitted_at": r_time})
        if r_user:
            users.append(r_user)
            if author and r_user != author:
                interactions.append({"reviewer": r_user, "author": author, "pr": pr_number})
    return events, interactions, users

def _process_review_comments(pr_number, author):
    comments = get_paginated_data(
        f"{BASE_URL}/pulls/{pr_number}/comments",
        where=f"review comments #{pr_number}"
    ) or []
    interactions, users, results = [], [], []
    for c in comments:
        c_user = (c.get("user") or {}).get("login")
        results.append({
            "pr": pr_number,
            "comment_id": c.get("id"),
            "commenter": c_user,
            "created_at": c.get("created_at"),
            "updated_at": c.get("updated_at"),
            "path": c.get("path"),
            "type": "review_comment",
            "body": c.get("body")
        })
        if c_user:
            users.append(c_user)
            if author and c_user != author:
                interactions.append({"reviewer": c_user, "author": author, "pr": pr_number})
    return results, interactions, users

def _process_issue_comments(pr_number, author):
    comments = get_paginated_data(
        f"{BASE_URL}/issues/{pr_number}/comments",
        where=f"issue comments #{pr_number}"
    ) or []
    interactions, users, results = [], [], []
    for c in comments:
        c_user = (c.get("user") or {}).get("login")
        results.append({
            "pr": pr_number,
            "comment_id": c.get("id"),
            "commenter": c_user,
            "created_at": c.get("created_at"),
            "updated_at": c.get("updated_at"),
            "path": None,
            "type": "issue_comment",
            "body": c.get("body")
        })
        if c_user:
            users.append(c_user)
            if author and c_user != author:
                interactions.append({"reviewer": c_user, "author": author, "pr": pr_number})
    return results, interactions, users

def _summarize_pr(pr, reviewers, rev_comment_users, issue_comment_users):
    created_at = pr.get("created_at")
    merged_at = pr.get("merged_at")
    closed_at = pr.get("closed_at")
    state = pr.get("state")
    author = (pr.get("user") or {}).get("login")
    title = pr.get("title", "")

    ttm_days = None
    if merged_at:
        ttm_days = (pd.to_datetime(merged_at) - pd.to_datetime(created_at)).total_seconds() / 86400.0

    return {
        "number": pr["number"],
        "title": title,
        "author": author,
        "state": state,
        "created_at": created_at,
        "closed_at": closed_at,
        "merged_at": merged_at,
        "time_to_merge_days": ttm_days,
        "total_reviews": len(reviewers),
        "total_review_comments": len(rev_comment_users),
        "total_issue_comments": len(issue_comment_users),
        "total_comments": len(rev_comment_users) + len(issue_comment_users),
        "reviewers": sorted(set(reviewers + rev_comment_users)),
        "commenters": sorted(set(issue_comment_users)),
    }

def fetch_pull_requests_with_details():
    prs = get_paginated_data(f"{BASE_URL}/pulls", params={"state":"all"}, where="pulls")
    pr_data, interactions, review_events, review_comments, issue_comments = [], [], [], [], []

    for pr in prs:
        pr_number = pr["number"]
        author = (pr.get("user") or {}).get("login")

        # Break into smaller steps
        r_events, r_interactions, reviewers = _process_reviews(pr_number, author)
        rc, rc_interactions, rev_comment_users = _process_review_comments(pr_number, author)
        ic, ic_interactions, issue_comment_users = _process_issue_comments(pr_number, author)

        # Collect
        review_events.extend(r_events)
        review_comments.extend(rc)
        issue_comments.extend(ic)
        interactions.extend(r_interactions + rc_interactions + ic_interactions)

        pr_data.append(_summarize_pr(pr, reviewers, rev_comment_users, issue_comment_users))

    return pr_data, interactions, review_events, review_comments, issue_comments

# ===== Issues =====
def fetch_issues():
    items = get_paginated_data(f"{BASE_URL}/issues", params={"state":"all"}, where="issues")
    # filter out PRs (issues endpoint includes PRs)
    return [i for i in items if "pull_request" not in i]

def resolve_issue_closer(issue_number):
    events = get_paginated_data(f"{BASE_URL}/issues/{issue_number}/events", where=f"issue events #{issue_number}")
    for ev in reversed(events or []):
        if ev.get("event") == "closed" and ev.get("actor"):
            return ev["actor"].get("login")
    return None

def issues_fixed_by(issues):
    fixed_map = defaultdict(int)
    for issue in issues:
        if issue.get("state") == "closed":
            closer = None
            if issue.get("closed_by") and (issue["closed_by"].get("login")):
                closer = issue["closed_by"]["login"]
            else:
                closer = resolve_issue_closer(issue["number"])
            if closer:
                fixed_map[closer] += 1
    return fixed_map

def top_reviewers_table(pr_df):
    counts = defaultdict(int)
    for _, row in pr_df.iterrows():
        for u in row["reviewers"]:
            counts[u] += 1
        for u in row["commenters"]:
            counts[u] += 1
    df = pd.DataFrame([{"user":k, "interactions":v} for k,v in counts.items()]).sort_values("interactions", ascending=False)
    return df

# ===== Save helpers =====
def save_contributors_csv(contributors):
    df = pd.DataFrame(contributors)
    df.to_csv("contributors.csv", index=False)
    print("✅ Saved contributors.csv")

def save_prs_csv(prs):
    df = pd.DataFrame(prs)
    df.to_csv("pull_requests.csv", index=False)
    print("✅ Saved pull_requests.csv")

def save_issues_csv(issues):
    df = pd.DataFrame(issues)
    df.to_csv("issues.csv", index=False)
    print("✅ Saved issues.csv")

def save_review_events_csv(review_events):
    df = pd.DataFrame(review_events)
    df.to_csv("review_events.csv", index=False)
    print("✅ Saved review_events.csv")

def save_review_comments_csv(review_comments):
    df = pd.DataFrame(review_comments)
    df.to_csv("review_comments.csv", index=False)
    print("✅ Saved review_comments.csv")

def save_issue_comments_csv(issue_comments):
    df = pd.DataFrame(issue_comments)
    df.to_csv("issue_comments.csv", index=False)
    print("✅ Saved issue_comments.csv")

def save_all_comments_csv(review_comments, issue_comments):
    """Combine both comment types into a single CSV for quick checks."""
    df1 = pd.DataFrame(review_comments)
    df2 = pd.DataFrame(issue_comments)
    df = pd.concat([df1, df2], ignore_index=True)
    df.to_csv("all_comments.csv", index=False)
    print("✅ Saved all_comments.csv")