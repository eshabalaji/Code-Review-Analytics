import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

# Cloud Run safe temp directory for saving files
DEFAULT_OUTPUT_DIR = "/tmp"

def setup_plot_style():
    """Sets up a clean, professional plot style."""
    sns.set_style("whitegrid")
    sns.set_palette("Paired")
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["font.size"] = 12
    plt.rcParams["axes.labelsize"] = 14
    plt.rcParams["axes.titlesize"] = 16
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10
    plt.rcParams["figure.titleweight"] = "bold"

def save_plot(filename, output_dir=None):
    """Saves the current plot to a file and closes it."""
    try:
        if output_dir is None:
            output_dir = DEFAULT_OUTPUT_DIR  # Use /tmp if nothing passed

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filepath = os.path.join(output_dir, filename)

        plt.tight_layout()
        plt.savefig(filepath)
        print(f"+ Saved plot to {filepath}")
    except Exception as e:
        print(f"❌ Failed to save plot {filename}: {e}")
    finally:
        plt.close()

def plot_commit_activity(date_count, output_dir):
    """Plots commit activity over time."""
    if not date_count:
        print("No commit data to plot.")
        return
    setup_plot_style()
    df = pd.DataFrame(date_count.items(), columns=['Date', 'Commits'])
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    plt.figure(figsize=(12, 6))
    plt.plot(df['Date'], df['Commits'], marker='o', linestyle='-')
    plt.title('Commit Activity Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Commits')
    plt.grid(True)
    plt.xticks(rotation=45)
    save_plot('commit_activity.png', output_dir)

def plot_author_activity(author_count, output_dir):
    """Plots top authors by commit count."""
    if not author_count:
        print("No author data to plot.")
        return
    setup_plot_style()
    top_authors = pd.DataFrame(author_count.items(), columns=['Author', 'Commits']).nlargest(10, 'Commits')

    plt.figure(figsize=(12, 8))
    sns.barplot(x='Commits', y='Author', data=top_authors, palette='viridis', hue='Author', legend=False)
    plt.title('Top 10 Commit Authors')
    plt.xlabel('Number of Commits')
    plt.ylabel('Author')
    plt.tight_layout()
    save_plot('author_activity.png', output_dir)

def plot_pr_timeline(pr_df, output_dir):
    """Plots the timeline of PRs (open and closed)."""
    if pr_df.empty:
        print("No PR timeline data to plot.")
        return
    setup_plot_style()
    pr_df['created_at'] = pd.to_datetime(pr_df['created_at'])
    pr_df['closed_at'] = pd.to_datetime(pr_df['closed_at'])

    plt.figure(figsize=(15, 8))
    
    open_prs = pr_df[pr_df['state'] == 'open']
    if not open_prs.empty:
        plt.scatter(open_prs['created_at'], [1]*len(open_prs), color='blue', label='Open PRs', s=100, alpha=0.6)

    closed_prs = pr_df[pr_df['state'].isin(['closed', 'merged'])]
    if not closed_prs.empty:
        plt.scatter(closed_prs['closed_at'], [0.5]*len(closed_prs), color='red', label='Closed PRs', s=100, alpha=0.6)
    
    plt.title('Pull Request Timeline')
    plt.xlabel('Date')
    plt.yticks([0.5, 1], ['Closed', 'Open'])
    plt.legend()
    plt.grid(True)
    save_plot('pr_timeline.png', output_dir)

def plot_prs_per_day(pr_df, output_dir):
    """Plots the number of PRs created each day."""
    if pr_df.empty:
        print("No PRs per day data to plot.")
        return
    setup_plot_style()
    pr_df['created_date'] = pd.to_datetime(pr_df['created_at']).dt.date
    prs_per_day = pr_df.groupby('created_date').size()
    
    plt.figure(figsize=(12, 6))
    prs_per_day.plot(kind='bar', color=sns.color_palette("Paired"))
    plt.title('Pull Requests Created Per Day')
    plt.xlabel('Date')
    plt.ylabel('Number of PRs')
    plt.xticks(rotation=45, ha='right')
    save_plot('prs_per_day.png', output_dir)

def plot_open_vs_closed_issues_counts(issues, output_dir):
    """Plots the count of open vs. closed issues."""
    if not issues:
        print("No issue data to plot.")
        return
    setup_plot_style()
    issue_states = [issue['state'] for issue in issues]
    df = pd.DataFrame(issue_states, columns=['State'])
    
    state_counts = df['State'].value_counts()
    
    plt.figure(figsize=(8, 8))
    plt.pie(state_counts, labels=state_counts.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("Set2"))
    plt.title('Open vs. Closed Issues Count')
    plt.axis('equal')
    save_plot('issues_count.png', output_dir)

def plot_issues_fixed_by(fixed_map, output_dir):
    """Plots a bar chart of issues fixed by user."""
    if not fixed_map:
        print("No issue fixed data to plot.")
        return
    setup_plot_style()
    df = pd.DataFrame(fixed_map.items(), columns=['Author', 'Issues Fixed'])
    df = df.sort_values('Issues Fixed', ascending=False)
    
    plt.figure(figsize=(12, 8))
    sns.barplot(x='Issues Fixed', y='Author', data=df, palette='Spectral')
    plt.title('Issues Fixed by User')
    plt.xlabel('Number of Issues Fixed')
    plt.ylabel('Author')
    save_plot('issues_fixed_by.png', output_dir)
