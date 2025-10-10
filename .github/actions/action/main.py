import pandas as pd
from datetime import datetime
import os
import sys
import json

# Add current folder to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from github_api import (
    fetch_repo_data, fetch_commits, group_commits_by_date_and_author,
    fetch_contributors, fetch_pull_requests_with_details, fetch_issues,
    issues_fixed_by, top_reviewers_table,
    save_contributors_csv, save_prs_csv, save_issues_csv,
    save_review_events_csv, save_review_comments_csv,
    save_issue_comments_csv, save_all_comments_csv
)
from visualisation import (
    plot_commit_activity, plot_author_activity, plot_pr_timeline,
    plot_prs_per_day, plot_open_vs_closed_issues_counts, plot_issues_fixed_by
)

import shutil
import logging

# Temporary folders
PLOTS_DIR = "/tmp/plots"
CSVS_DIR = "/tmp/csv"

def cleanup_temp_dirs():
    """Clean up old plots and CSV files before running analytics."""
    for folder in [PLOTS_DIR, CSVS_DIR]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                logging.info(f"Cleared old files in {folder}")
            except Exception as e:
                logging.warning(f"Failed to clear folder {folder}: {e}")
        os.makedirs(folder, exist_ok=True)

def main():
    # Clean old files
    cleanup_temp_dirs()

    repo_data = fetch_repo_data()
    if not repo_data:
        print("Failed to fetch repository data. Exiting.")
        return

    # Commits
    commits = fetch_commits()
    date_count, author_count = group_commits_by_date_and_author(commits)

    # Contributors
    contributors = fetch_contributors()

    # Format required repo info for frontend
    created = datetime.strptime(repo_data['created_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    updated = datetime.strptime(repo_data['updated_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")

    repo_stats = {
        "name": repo_data['name'],
        "owner": repo_data['owner']['login'],
        "stars": repo_data['stargazers_count'],
        "forks": repo_data['forks_count'],
        "open_issues": repo_data['open_issues_count'],
        "created_at": created,
        "updated_at": updated,
        "contributors": len(contributors)
    }

    # Send structured info to Flask
    print("---REPO-INFO-START---")
    print(json.dumps(repo_stats))
    print("---REPO-INFO-END---")

    # PRs
    pr_data, interactions, review_events, review_comments, issue_comments = fetch_pull_requests_with_details()
    pr_df = pd.DataFrame(pr_data)

    # Issues
    issues = fetch_issues()
    fixed_map = issues_fixed_by(issues)

    # === Plots ===
    plot_commit_activity(date_count, PLOTS_DIR)
    plot_author_activity(author_count, PLOTS_DIR)
    if not pr_df.empty:
        plot_pr_timeline(pr_df, PLOTS_DIR)
        plot_prs_per_day(pr_df, PLOTS_DIR)
    plot_open_vs_closed_issues_counts(issues, PLOTS_DIR)
    plot_issues_fixed_by(fixed_map, PLOTS_DIR)

    # === Save CSVs ===
    # If your github_api functions don't support folder, call without extra argument
    save_contributors_csv(contributors)      # old version: saves to default location
    save_prs_csv(pr_data)
    save_issues_csv(issues)
    save_review_events_csv(review_events)
    save_review_comments_csv(review_comments)
    save_issue_comments_csv(issue_comments)
    save_all_comments_csv(review_comments, issue_comments)

if __name__ == "__main__":
    main()
