import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import tempfile
import sys # For printing errors to stderr

# Define consistent temp path
TEMP_ROOT = os.path.join(tempfile.gettempdir(), 'github_analytics')
PLOTS_DIR = os.path.join(TEMP_ROOT, 'plots')


def save_plot(fig, plot_filename, output_dir=PLOTS_DIR):
    """Save plot to the specified output directory and close the figure."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, plot_filename)

    try:
        # Save the specific figure object
        fig.savefig(filepath)
        # Close the figure to free up memory (important in web apps)
        plt.close(fig) 
        return filepath
    except Exception as e:
        print(f"Error saving plot {plot_filename}: {e}", file=sys.stderr)
        return None

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


# --- Plotting Functions (All updated to return fig object and use correct save_plot) ---

def plot_commit_activity(date_count, output_dir):
    """Plots commit activity over time."""
    if not date_count:
        return
    setup_plot_style()
    df = pd.DataFrame(date_count.items(), columns=['Date', 'Commits'])
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    fig = plt.figure(figsize=(12, 6))
    plt.plot(df['Date'], df['Commits'], marker='o', linestyle='-')
    plt.title('Commit Activity Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Commits')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    save_plot(fig, 'commit_activity.png', output_dir)

def plot_author_activity(author_count, output_dir):
    """Plots top authors by commit count."""
    if not author_count:
        return
    setup_plot_style()
    top_authors = pd.DataFrame(author_count.items(), columns=['Author', 'Commits']).nlargest(10, 'Commits')

    fig = plt.figure(figsize=(12, 8))
    sns.barplot(x='Commits', y='Author', data=top_authors, palette='viridis', hue='Author', legend=False)
    plt.title('Top 10 Commit Authors')
    plt.xlabel('Number of Commits')
    plt.ylabel('Author')
    plt.tight_layout()
    save_plot(fig, 'author_activity.png', output_dir)

def plot_pr_timeline(pr_df, output_dir):
    """Plots the timeline of PRs (open and closed)."""
    if pr_df.empty:
        return
    setup_plot_style()
    pr_df['created_at'] = pd.to_datetime(pr_df['created_at'])
    pr_df['closed_at'] = pd.to_datetime(pr_df['closed_at'])

    fig = plt.figure(figsize=(15, 8))
    
    open_prs = pr_df[pr_df['state'] == 'open']
    if not open_prs.empty:
        plt.scatter(open_prs['created_at'], [1]*len(open_prs), color='blue', label='Open PRs', s=100, alpha=0.6)

    closed_prs = pr_df[pr_df['state'].isin(['closed', 'merged'])]
    if not closed_prs.empty:
        plt.scatter(closed_prs['closed_at'], [0.5]*len(closed_prs), color='red', label='Closed/Merged PRs', s=100, alpha=0.6)
    
    plt.title('Pull Request Timeline')
    plt.xlabel('Date')
    plt.yticks([0.5, 1], ['Closed/Merged', 'Open'])
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    save_plot(fig, 'pr_timeline.png', output_dir)

def plot_prs_per_day(pr_df, output_dir):
    """Plots the number of PRs created each day."""
    if pr_df.empty:
        return
    setup_plot_style()
    pr_df['created_date'] = pd.to_datetime(pr_df['created_at']).dt.date
    prs_per_day = pr_df.groupby('created_date').size()
    
    fig = plt.figure(figsize=(12, 6))
    prs_per_day.plot(kind='bar', color=sns.color_palette("Paired"))
    plt.title('Pull Requests Created Per Day')
    plt.xlabel('Date')
    plt.ylabel('Number of PRs')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    save_plot(fig, 'prs_per_day.png', output_dir)

def plot_open_vs_closed_issues_counts(issues, output_dir):
    """Plots the count of open vs. closed issues."""
    if not issues:
        return
    setup_plot_style()
    issue_states = [issue['state'] for issue in issues]
    df = pd.DataFrame(issue_states, columns=['State'])
    
    state_counts = df['State'].value_counts()
    
    fig = plt.figure(figsize=(8, 8))
    plt.pie(state_counts, labels=state_counts.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("Set2"))
    plt.title('Open vs. Closed Issues Count')
    plt.axis('equal')
    save_plot(fig, 'issues_count.png', output_dir)

def plot_issues_fixed_by(fixed_map, output_dir):
    """Plots a bar chart of issues fixed by user."""
    if not fixed_map:
        return
    setup_plot_style()
    df = pd.DataFrame(fixed_map.items(), columns=['Author', 'Issues Fixed'])
    df = df.sort_values('Issues Fixed', ascending=False).nlargest(10, 'Issues Fixed')
    
    fig = plt.figure(figsize=(12, 8))
    sns.barplot(x='Issues Fixed', y='Author', data=df, palette='Spectral', hue='Author', legend=False)
    plt.title('Top 10 Users by Issues Fixed')
    plt.xlabel('Number of Issues Fixed')
    plt.ylabel('Author')
    plt.tight_layout()
    save_plot(fig, 'issues_fixed_by.png', output_dir)