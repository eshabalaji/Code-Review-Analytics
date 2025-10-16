# .github/actions/action/main.py
import pandas as pd
from datetime import datetime
import os
import sys
import json
import traceback
import logging
import tempfile # <--- ADDED

# Import all necessary functions
from github_api import (
    fetch_repo_data, fetch_commits, group_commits_by_date_and_author,
    fetch_contributors, fetch_pull_requests_with_details, fetch_issues,
    issues_fixed_by,
    save_contributors_csv, save_prs_csv, save_issues_csv,
    save_review_events_csv, save_review_comments_csv,
    save_issue_comments_csv, save_all_comments_csv)

from visualisation import (
    plot_commit_activity, plot_author_activity, plot_pr_timeline,
    plot_prs_per_day, plot_open_vs_closed_issues_counts, plot_issues_fixed_by)

# Define consistent temp paths
TEMP_ROOT = os.path.join(tempfile.gettempdir(), 'github_analytics')
PLOTS_DIR = os.path.join(TEMP_ROOT, 'plots')
CSVS_DIR = os.path.join(TEMP_ROOT, 'csv')

# Configure logging for the script
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ensure local imports work
sys.path.append(os.path.dirname(__file__))

def cleanup_temp_dirs():
    """Ensure output directories exist, creating them if necessary."""
    for folder in [PLOTS_DIR, CSVS_DIR]:
        os.makedirs(folder, exist_ok=True)


def main():
    try:
        cleanup_temp_dirs()
        logging.info(f"Output directories ensured: {PLOTS_DIR} and {CSVS_DIR}")

        repo_data = fetch_repo_data()
        if not repo_data:
            print("Failed to fetch repository data. Exiting.", file=sys.stderr)
            sys.exit(1)

        commits = fetch_commits()
        date_count, author_count = group_commits_by_date_and_author(commits)
        contributors = fetch_contributors()

        created = datetime.strptime(repo_data.get('created_at', datetime.min.isoformat()), "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
        updated = datetime.strptime(repo_data.get('updated_at', datetime.min.isoformat()), "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")

        repo_stats = {
            "name": repo_data.get('name', 'Unknown'),
            "owner": repo_data['owner']['login'],
            "stars": repo_data.get('stargazers_count', 0),
            "forks": repo_data.get('forks_count', 0),
            "open_issues": repo_data.get('open_issues_count', 0),
            "created_at": created,
            "updated_at": updated,
            "contributors": len(contributors)
        }

        # Print structured JSON for app.py to parse
        print("---REPO-INFO-START---")
        print(json.dumps(repo_stats))
        print("---REPO-INFO-END---")

        pr_data, interactions, review_events, review_comments, issue_comments = fetch_pull_requests_with_details()
        pr_df = pd.DataFrame(pr_data)

        issues = fetch_issues()
        fixed_map = issues_fixed_by(issues)
        
        # --- Plotting ---
        plot_commit_activity(date_count, PLOTS_DIR)
        plot_author_activity(author_count, PLOTS_DIR)
        if not pr_df.empty:
            plot_pr_timeline(pr_df, PLOTS_DIR)
            plot_prs_per_day(pr_df, PLOTS_DIR)
        plot_open_vs_closed_issues_counts(issues, PLOTS_DIR)
        plot_issues_fixed_by(fixed_map, PLOTS_DIR)
        
        # --- CSV saving ---
        save_contributors_csv(contributors)
        save_prs_csv(pr_data)
        save_issues_csv(issues)
        save_review_events_csv(review_events)
        save_review_comments_csv(review_comments)
        save_issue_comments_csv(issue_comments)
        save_all_comments_csv(review_comments, issue_comments)

    except SystemExit:
        # Allow SystemExit to propagate (e.g., from github_api's _initialize_globals)
        raise
    except Exception as e:
        print("---UNCAUGHT-EXCEPTION-START---", file=sys.stderr)
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("---UNCAUGHT-EXCEPTION-END---", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()