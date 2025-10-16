# 🚀 Code Review Analytics

A **web-based tool** for fetching, analyzing, and visualizing key metrics from any public or private GitHub repository using a **Python Flask backend**.

---

## 🔎 About

This project provides a **self-hosted analytics solution** for developers and managers to gain deep insights into repository health, development velocity, and team contributions.  

The application separates the web interface (**Flask/HTML**) from the analytics engine (`main.py`), allowing robust, long-running analytics tasks to execute as subprocesses on the server.

It is configured to run with **Gunicorn**, making it production-ready for environments like **AWS ECS**, **Fargate**, or **App Runner**.

---

## ✨ Features

- **Dynamic Analysis** – Executes `main.py` as a subprocess to run analytics on demand, ensuring fresh data.
- **Token-Based Access** – Securely handles GitHub Personal Access Tokens (PATs) for private repositories.
- **Visualization Suite** – Generates plots such as:
  - Commit Activity  
  - PR Time to Merge  
  - Reviewer–Author Heatmaps  
  - Issue Counts  
- **Raw Data Access** – View or download generated CSV datasets.
- **Non-Blocking Execution** – Uses subprocess management in Flask to avoid blocking during long operations.

---

## 📂 File Structure

The project maintains a clear separation between the web environment and the analytics engine, which is located in a dedicated subdirectory:
```
├── app.py                      # Flask Web Server (uses Gunicorn in production)
├── templates/
│   └── dashboard.html          # Main application interface
├── .github/
│   └── actions/
│       └── action/             # The core analytics engine directory
│             ├── main.py            # Orchestrates data fetching and plotting
│             ├── github_api.py      # API communication utilities
│             ├── visualisation.py   # Plotting functions
├── Dockerfile                  # Container definition for production deployment
└── requirements.txt            # Python dependencies
```

---

## 🧠 How It Works

The application operates on a **client–server–subprocess model**:

1. **Client Request:**  
   The user clicks the **"Run Analytics"** button in `dashboard.html`.

2. **Server Execution (Gunicorn):**  
   An AJAX POST request is sent to the `/run-analytics` route in `app.py`.

3. **Subprocess Orchestration:**  
   `app.py` captures parameters (`owner`, `repo`, `token`) and executes `main.py` as a separate, time-limited Python process.

4. **Data Generation:**  
   `main.py` fetches data via the GitHub API, processes it, and saves results to temporary directories:  
   `/tmp/github_analytics/plots` and `/tmp/github_analytics/csv`.

5. **Server Response:**  
   Flask sends a JSON response (`status: success`) back to the client when execution completes.

6. **Data Display:**  
   The frontend JavaScript in `dashboard.html` updates the UI to display plots and CSV tables.

---

## ⚙️ Prerequisites
  
- **GitHub Personal Access Token (PAT)** – Needed for authentication and higher API rate limits.

---

## 🐍 Python Dependencies

Listed in `requirements.txt`:

| Library | Purpose |
|----------|----------|
| Flask | Core web framework for backend |
| requests | GitHub API communication |
| pandas | Data manipulation and analysis |
| matplotlib | Core plotting library |
| seaborn | Statistical data visualization |
| gunicorn | Production WSGI HTTP server |

---

## ☁️ Deploy to AWS

### 🧩 Push to ECR
Tag and push your Docker image to your **Amazon EC2** repository.

### 🚀 Deploy
Use your ECR image with services like **AWS Fargate** or **AWS App Runner**.  
These services automatically execute the **Gunicorn** command defined in the `Dockerfile`.

---

## 🔑 Configuration

The dashboard collects the following runtime parameters (entered by the user):

| **Parameter** | **Location** | **Description** |
|----------------|--------------|-----------------|
| **Owner** | Input Field | GitHub organization or username (e.g., `kubernetes`) |
| **Repo** | Input Field | Repository name (e.g., `kubernetes`) |
| **Token** | Input Field | GitHub Personal Access Token (PAT) |

---

## ▶️ Usage

### 🏁 Start the Application
 run locally using **Gunicorn**.

### 📈 Generate Analytics
1. Visit: [http://localhost:8080/dashboard](http://localhost:8080/dashboard)  
2. Enter **Owner**, **Repo**, and **Token**.  
3. Click **Run Analytics** and wait for results (max 120 seconds).

### 📊 View Data
- Open the **Plots** tab for visual insights.  
- Open the **CSV Data** tab to view or download raw datasets.

---

## 📊 Dashboard Output

Once analysis completes successfully, the dashboard displays results in **two main tabs**:

### 1️⃣ Plots Tab (Visualizations)

| **Plot** | **Description** |
|-----------|-----------------|
| `commit_activity.png` | Time series of commit volume over time |
| `author_activity.png` | Breakdown of commits per contributor |
| `time_to_merge.png` | Distribution of PR merge times |
| `reviewer_author_heatmap.png` | Reviewer–Author interaction matrix |

---

### 2️⃣ CSV Data Tab (Raw Data)

- Displays links to raw CSV files generated in `.github/actions/action/csv/`.
- **View Button:** Opens CSV preview in a scrollable modal table.  
- **Download Button:** Downloads the full CSV file (e.g., `prs.csv`, `issues.csv`).

---

## 🛠️ Tech Stack

| **Component** | **Technology** |
|----------------|----------------|
| **Backend** | Flask (Python) |
| **Frontend** | HTML, CSS, JavaScript |
| **Data Analysis** | Pandas, Matplotlib, Seaborn |
| **Server** | Gunicorn |
| **Cloud** | AWS (ECR, ECS, Fargate, or App Runner) |

---
