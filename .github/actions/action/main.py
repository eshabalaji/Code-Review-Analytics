import pandas as pd
from datetime import datetime
from github_api import (
    fetch_repo_data, fetch_commits, group_commits_by_date_and_author,
    fetch_contributors, fetch_pull_requests_with_details, fetch_issues,
    issues_fixed_by, top_reviewers_table, save_contributors_csv, save_prs_csv,
    save_issues_csv, save_review_events_csv, save_review_comments_csv,
    save_issue_comments_csv, save_all_comments_csv
)
from visualisation import (
    plot_commit_activity, plot_author_activity, plot_pr_timeline,
    plot_prs_per_day, plot_open_vs_closed_issues_counts, plot_issues_fixed_by,
    plot_reviewer_author_heatmap, plot_time_to_merge
)

# ===== Main =====
def main():
    repo_data = fetch_repo_data()
    if not repo_data:
        return

    print(f"Repository: {repo_data['name']}")
    print(f"Description: {repo_data['description']}")
    print(f"Stars: {repo_data['stargazers_count']}, Forks: {repo_data['forks_count']}")
    print(f"Open Issues (incl PRs): {repo_data['open_issues_count']}")
    created = datetime.strptime(repo_data['created_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    updated = datetime.strptime(repo_data['updated_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    print(f"Created: {created}, Updated: {updated}")

    # Commits
    commits = fetch_commits()
    date_count, author_count = group_commits_by_date_and_author(commits)

    # Contributors
    contributors = fetch_contributors()
    print(f"Total Contributors: {len(contributors)}")

    # PRs (detailed) + interactions + explicit commenters/reviewers artifacts
    pr_data, interactions, review_events, review_comments, issue_comments = fetch_pull_requests_with_details()
    pr_df = pd.DataFrame(pr_data)

    print("\nPull Request Data (top 15 rows):")
    if not pr_df.empty:
        print(pr_df[["number","title","author","state","created_at","merged_at","time_to_merge_days","total_comments"]]
              .head(15).to_string(index=False))
    else:
        print("No PRs found.")

    # Show evidence that commenters were captured (mentor ask)
    total_commenters = sum(len(x) for x in pr_df.get("commenters", [])) if not pr_df.empty else 0
    total_reviewers = sum(len(x) for x in pr_df.get("reviewers", [])) if not pr_df.empty else 0
    print(f"\nCaptured reviewers list across PRs: {total_reviewers}")
    print(f"Captured commenters list across PRs: {total_commenters}")
    print(f"Review events: {len(review_events)} | Review comments: {len(review_comments)} | Issue comments: {len(issue_comments)}")

    # Reviewers (top table)
    reviewers_df = top_reviewers_table(pr_df) if not pr_df.empty else pd.DataFrame(columns=["user","interactions"])
    if not reviewers_df.empty:
        print("\nTop reviewers & commenters (by interactions):")
        print(reviewers_df.head(15).to_string(index=False))

    # Issues & who fixed them
    issues = fetch_issues()
    fixed_map = issues_fixed_by(issues)
    if fixed_map:
        print("\nIssues fixed by user:")
        fix_df = pd.DataFrame(fixed_map.items(), columns=["user","issues_fixed"]).sort_values("issues_fixed", ascending=False)
        print(fix_df.to_string(index=False))
    else:
        print("\nNo fixed issue data (or unable to resolve closers).")

    # === Plots ===
    plot_commit_activity(date_count)
    plot_author_activity(author_count)
    if not pr_df.empty:
        plot_pr_timeline(pr_df)
        plot_prs_per_day(pr_df)
        plot_reviewer_author_heatmap(interactions)
        plot_time_to_merge(pr_df)
    plot_open_vs_closed_issues_counts(issues)
    plot_issues_fixed_by(fixed_map)

    # === Save CSVs (incl. commenters artifacts) ===
    save_contributors_csv(contributors)
    save_prs_csv(pr_data)
    save_issues_csv(issues)
    save_review_events_csv(review_events)
    save_review_comments_csv(review_comments)
    save_issue_comments_csv(issue_comments)
    save_all_comments_csv(review_comments, issue_comments)

if __name__ == "__main__":
    main()