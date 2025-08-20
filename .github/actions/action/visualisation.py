import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ===== Visualizations =====
def plot_commit_activity(date_count):
    if not date_count:
        print("No commits to plot.")
        return
    df = pd.DataFrame(sorted(date_count.items()), columns=['Date', 'Commits'])
    plt.figure(figsize=(7,4))
    sns.lineplot(data=df, x='Date', y='Commits', marker='o')
    plt.title('Commits per Day')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_author_activity(author_count):
    if not author_count:
        print("No author commit data to plot.")
        return
    df = pd.DataFrame(author_count.items(), columns=['Author', 'CommitCount']).sort_values(by='CommitCount', ascending=False)
    plt.figure(figsize=(7,4))
    sns.barplot(data=df, x='Author', y='CommitCount')
    plt.title('Commits per Contributor')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_pr_timeline(pr_df):
    if pr_df.empty:
        print("No PRs to plot timeline.")
        return
    df = pr_df.copy()
    df['created_at'] = pd.to_datetime(df['created_at'])
    df_open = df[df['state'] == 'open']
    df_closed = df[df['state'] == 'closed']

    plt.figure(figsize=(7,4))
    plt.hist(df_open['created_at'], bins=10, alpha=0.7, label='Open PRs')
    plt.hist(df_closed['created_at'], bins=10, alpha=0.7, label='Closed PRs')
    plt.legend()
    plt.title('PRs Created Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of PRs')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_prs_per_day(pr_df):
    if pr_df.empty:
        print("No PRs to plot per-day.")
        return
    s = pd.to_datetime(pr_df["created_at"]).dt.date.value_counts().sort_index()
    plt.figure(figsize=(7,4))
    plt.plot(s.index, s.values, marker="o")
    plt.title("PRs per Day")
    plt.xlabel("Date")
    plt.ylabel("PR count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_open_vs_closed_issues_counts(issues):
    open_count = sum(1 for i in issues if i['state'] == 'open')
    closed_count = sum(1 for i in issues if i['state'] == 'closed')

    plt.figure(figsize=(6,4))
    plt.bar(['Open', 'Closed'], [open_count, closed_count])
    plt.title('Open vs Closed Issues (Count)')
    plt.ylabel('Number of Issues')
    for idx, count in enumerate([open_count, closed_count]):
        plt.text(idx, count + 0.5, str(count), ha='center', fontsize=11)
    plt.tight_layout()
    plt.show()

def plot_issues_fixed_by(fixed_map):
    if not fixed_map:
        print("No closed issues with resolvers to plot.")
        return
    df = pd.DataFrame(fixed_map.items(), columns=['User', 'Issues Fixed']).sort_values(by='Issues Fixed', ascending=False)
    plt.figure(figsize=(7,4))
    sns.barplot(data=df, x='User', y='Issues Fixed')
    plt.title('Issues Fixed by Contributor')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_reviewer_author_heatmap(interactions):
    if not interactions:
        print("No reviewer/author interactions to plot.")
        return
    df = pd.DataFrame(interactions)
    pivot = df.pivot_table(index="reviewer", columns="author", values="pr", aggfunc="nunique", fill_value=0)
    plt.figure(figsize=(max(6, 0.6*len(pivot.columns)), max(4, 0.6*len(pivot.index))))
    sns.heatmap(pivot, annot=True, fmt="d", cbar=True)
    plt.title("Who Reviews Whom (PR count)")
    plt.tight_layout()
    plt.show()

def plot_time_to_merge(pr_df):
    merged = pr_df[pr_df["time_to_merge_days"].notna()]
    if merged.empty:
        print("No merged PRs to plot time-to-merge.")
        return
    plt.figure(figsize=(7,4))
    plt.hist(merged["time_to_merge_days"], bins=10)
    plt.title("Time to Merge (days)")
    plt.xlabel("Days")
    plt.ylabel("PR count")
    plt.tight_layout()
    plt.show()