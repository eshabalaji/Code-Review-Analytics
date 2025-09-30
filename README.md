# Code Review Analytics

A web-based tool for fetching, analyzing, and visualizing key metrics from any public or private GitHub repository using a Python Flask backend.

---

## 🔎 About

This project provides a self-hosted solution for developers and managers to gain deep insights into repository health, development velocity, and team contributions. The application separates the web interface (Flask/HTML) from the data processing engine (`main.py`), allowing for robust, long-running analytics tasks to be executed as a subprocess on the server.

## ✨ Features

* **Dynamic Analysis:** Executes a Python subprocess (`main.py`) to run analytics on demand, ensuring data is always fresh.
* **Token-Based Access:** Securely handles GitHub Personal Access Tokens (PATs) passed via the frontend for analyzing private repositories.
* **Visualization Suite:** Generates and displays a suite of plots, including Commit Activity, PR Time to Merge, Reviewer-Author Heatmaps, and Issue Counts.
* **Raw Data Access:** Provides direct viewing and download links for raw CSV data tables.
* **Non-Blocking Execution:** Uses robust subprocess management in Flask to prevent the web server from hanging during long-running data fetches.

## 📂 File Structure

The project maintains a clear separation between the web environment and the analytics engine:
```txt
├── app.py                     
├── templates/
│   ├── index.html              
│   └── dashboard.html         
├── .github/
│   └── actions/
│       └── action/             
│             ├── main.py       
│             ├── github_api.py 
│             ├── visualisation.py 
│             ├── csv/          
│             └── plots/        
└── requirements.txt           
             
```

## 🧠 How It Works

The application operates on a client-server-subprocess model:

1.  **Client Request:** The user clicks the "Run Analytics" button on the `dashboard.html` (Client).
2.  **Server Execution:** An AJAX `POST` request is sent to the `/run-analytics` route in `app.py` (Flask Server).
3.  **Subprocess Orchestration:** `app.py` captures the necessary parameters (owner, repo, token) and executes `main.py` as a separate, time-limited Python process (`subprocess.run`).
4.  **Data Generation:** `main.py` fetches data, processes it using helper scripts, and writes all plots (`.png`) and CSVs to the `plots/` and `csv/` subdirectories.
5.  **Server Response:** Once `main.py` successfully completes, Flask sends a JSON response back to the client (`status: success`).
6.  **Data Display:** The client-side JavaScript (`dashboard.html`) receives the success signal and triggers a refresh, fetching the newly generated files via the `/plots/<filename>` and `/csv/<filename>` routes.

## ⚙️ Prerequisites

* **Python 3.8+**
* **`pip`** (Python package installer)

## 🐍 Python Dependencies

The core application requires the following libraries, which must be installed in your environment (as specified in `requirements.txt`):

| Library | Purpose |
| :--- | :--- |
| **`Flask`** | Core web framework for the backend server (`app.py`). |
| **`requests`** | Used in `github_api.py` for making HTTP calls to the GitHub API. |
| **`pandas`** | Essential for data manipulation, cleaning, and analysis in `main.py`. |
| **`matplotlib`** | Base plotting library for creating visualizations. |
| **`seaborn`** | Visualization library built on Matplotlib for statistical plots. |

## 💻 Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [your-repo-link]
    cd [your-repo-name]
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate # macOS/Linux
    # venv\Scripts\activate # Windows
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🔑 Configuration

The application requires runtime configuration via URL parameters and input fields:

### GitHub Personal Access Token (PAT)

A PAT is **required** to authenticate with the GitHub API, preventing rate limiting and allowing access to private repositories.

* The PAT must be provided in the dashboard input.

### Repository Details

The dashboard requires the following input fields, which are passed to the backend via the client-side JavaScript:

| Parameter | Location | Description |
| :--- | :--- | :--- |
| **Owner** | Input Field | The GitHub organization or user name (e.g., `kubernetes`). |
| **Repo** | Input Field | The repository name (e.g., `kubernetes`). |
| **Token** | Input Field | The user's GitHub Personal Access Token (PAT). |

## ▶️ Usage

1.  **Start the Flask Server:**
    ```bash
    python app.py
    ```
    (Access the app at `http://127.0.0.1:5000/dashboard`)

2.  **Generate Report:**
    * Enter the **Owner**, **Repo**, and **Token** in the dashboard form.
    * Click **Run Analytics**.
    * Wait for the process to complete (max 120 seconds). The plots tab will activate automatically upon success.

3.  **View Data:**
    * Use the **Plots** tab to see visualizations.
    * Use the **CSV Data** tab to view and download raw data files.

## 📊 Output Format (Dashboard Display)

Once the analytics script completes successfully, the dashboard switches from the **"Running..."** status to displaying the results, organized into two main, clickable tabs:

---

### 1. Plots Tab (Visualizations)
This tab displays all the generated **PNG image files** fetched from the server's `/plots/` endpoint.  
These visualizations provide immediate insight into repository activity and health:

| Example Plot                  | Data Displayed                                                                 |
|--------------------------------|--------------------------------------------------------------------------------|
| **commit_activity.png**        | Time series of commit volume over the selected period.                         |
| **author_activity.png**        | Breakdown of commits/contributions by individual authors.                      |
| **time_to_merge.png**          | Distribution (histogram) of the time taken for Pull Requests to be merged.     |
| **reviewer_author_heatmap.png**| Matrix showing interactions between reviewers and authors.                     |

---

### 2. CSV Data Tab (Raw Data)
This tab displays links to the **raw data files** generated and saved to the  
`.github/actions/action/csv/` directory. Users can interact with the raw data in two ways:

- **View Button**: Opens a responsive modal pop-up that displays a preview of the CSV content  
  as a scrollable **HTML table**, ideal for quick inspection.
- **Download Button**: Triggers a direct file download of the full CSV file (e.g., `prs.csv`, `issues.csv`)  
  to the user's local machine for further analysis in external tools.
