import os
import sys
import requests
import pandas as pd
from datetime import datetime
from collections import defaultdict
import logging
import tempfile # <--- ADDED

# --- PATH CONFIGURATION (CRITICAL FIX) ---
TEMP_ROOT = os.path.join(tempfile.gettempdir(), 'github_analytics')
CSVS_DIR = os.path.join(TEMP_ROOT, 'csv') # <--- FIXED PATH

HEADERS = {}
BASE_URL = ""
OWNER = ""
REPO = ""

def _initialize_globals():
    global OWNER, REPO, HEADERS, BASE_URL
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    OWNER = os.getenv("OWNER")
    REPO = os.getenv("REPO")

    missing_vars = [v for v, val in {
        "OWNER": OWNER,
        "REPO": REPO
    }.items() if not val]

    if missing_vars:
        logging.error(f"Missing critical environment vars: {', '.join(missing_vars)}. Analysis cannot run.")
        raise SystemExit(1)

    HEADERS = {
        'Accept': 'application/vnd.github.v3+json'
    }
    if GITHUB_TOKEN:
        HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'
    
    BASE_URL = f'https://api.github.com/repos/{OWNER}/{REPO}'

try:
    _initialize_globals()
except SystemExit:
    sys.exit(1)


def _log_http_error(resp, where=""):
    try:
        err = resp.json()
    except ValueError:
        err = {"message": resp.text}
    logging.error(f"HTTP {resp.status_code} while {where}: {err}")


def get_paginated_data(url, params=None, where="GET (paginated)"):
    params = params or {}
    params.setdefault("per_page", 100)
    results, page = [], 1

    if not BASE_URL:
        return []

    while True:
        q = dict(params)
        q["page"] = page
        resp = requests.get(url, headers=HEADERS, params=q)
        if resp.status_code != 200:
            _log_http_error(resp, where=f"{where} (page {page})")
            break

        batch = resp.json()
        if not isinstance(batch, list) or not batch:
            break

        results.extend(batch)
        # Check if the last page was returned
        if 'link' not in resp.headers and len(batch) < params["per_page"]:
            break
        # Proper check for link header to continue pagination (better than relying on batch size)
        if 'rel="next"' not in resp.headers.get('link', ''):
             break
        
        page += 1

    return results


# === Fetch functions ===
def fetch_repo_data():
    res = requests.get(BASE_URL, headers=HEADERS)
    return res.json() if res.status_code == 200 else None


def fetch_commits():
    return get_paginated_data(f'{BASE_URL}/commits', where="commits")


def group_commits_by_date_and_author(commits):
    date_count = defaultdict(int)
    author_count = defaultdict(int)
    for commit in commits:
        try:
            date_str = commit['commit']['author']['date']
            date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").date()
            author = commit['commit']['author'].get('name') or (commit.get('author') or {}).get('login') or "Unknown"
            date_count[date] += 1
            author_count[author] += 1
        except Exception as e:
            logging.warning(f"Skipping malformed commit data: {e}")
            continue
    return date_count, author_count


def fetch_contributors():
    return get_paginated_data(f'{BASE_URL}/contributors', where="contributors")


# === Pull Requests ===
def fetch_pull_requests_with_details():
    prs = get_paginated_data(f"{BASE_URL}/pulls", params={"state": "all"}, where="pulls")
    pr_data, interactions, review_events, review_comments, issue_comments = [], [], [], [], []
    for pr in prs:
        author = (pr.get("user") or {}).get("login")
        pr_data.append({
            "number": pr["number"],
            "title": pr.get("title", ""),
            "author": author,
            "state": pr.get("state", ""),
            "created_at": pr.get("created_at"),
            "merged_at": pr.get("merged_at"),
            "closed_at": pr.get("closed_at"),
        })
    return pr_data, interactions, review_events, review_comments, issue_comments


def fetch_issues():
    items = get_paginated_data(f"{BASE_URL}/issues", params={"state": "all"}, where="issues")
    # Filter out pull requests which are also returned by the /issues endpoint
    return [i for i in items if "pull_request" not in i]


def issues_fixed_by(issues):
    fixed_map = defaultdict(int)
    for issue in issues:
        if issue.get("state") == "closed":
            # Issues closed by PR merges will have the merged_by user in the last commit (too complex for this API scope)
            # The closed_by field is typically set if it's closed by a commit with a closing keyword, or by a user manually.
            closer = (issue.get("closed_by") or {}).get("login")
            if closer:
                fixed_map[closer] += 1
    return fixed_map


# === CSV saving ===
def save_dataframe_to_csv(data, filename, output_dir=CSVS_DIR):
    if not data:
        return
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    path = os.path.join(output_dir, filename)
    
    # Convert list of dicts to DataFrame for consistent handling
    try:
        pd.DataFrame(data).to_csv(path, index=False)
        logging.info(f"Saved {filename} to {path}")
    except Exception as e:
        logging.error(f"Failed to save CSV {filename}: {e}")


def save_contributors_csv(contributors): save_dataframe_to_csv(contributors, "contributors.csv")
def save_prs_csv(pr_data): save_dataframe_to_csv(pr_data, "pull_requests.csv")
def save_issues_csv(issues): save_dataframe_to_csv(issues, "issues.csv")
def save_review_events_csv(events): save_dataframe_to_csv(events, "review_events.csv")
def save_review_comments_csv(comments): save_dataframe_to_csv(comments, "review_comments.csv")
def save_issue_comments_csv(comments): save_dataframe_to_csv(comments, "issue_comments.csv")
def save_all_comments_csv(r_comments, i_comments):
    save_dataframe_to_csv(r_comments + i_comments, "all_comments.csv")