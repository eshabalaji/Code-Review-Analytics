Code Review Analytics
A web-based tool for fetching, analyzing, and visualizing key metrics from any public or private GitHub repository using a Python Flask backend.

🔎 About
This project provides a self-hosted solution for developers and managers to gain deep insights into repository health, development velocity, and team contributions. The application separates the web interface (Flask/HTML) from the data processing engine (main.py), allowing for robust, long-running analytics tasks to be executed as a subprocess on the server.

The application is containerized using Docker and is configured to run with Gunicorn, making it ready for production environments like AWS ECS, Fargate, or App Runner.

✨ Features
Dynamic Analysis: Executes a Python subprocess (main.py) to run analytics on demand, ensuring data is always fresh.

Token-Based Access: Securely handles GitHub Personal Access Tokens (PATs) passed via the frontend for analyzing private repositories.

Visualization Suite: Generates and displays a suite of plots, including Commit Activity, PR Time to Merge, Reviewer-Author Heatmaps, and Issue Counts.

Raw Data Access: Provides direct viewing and download links for raw CSV data tables.

Non-Blocking Execution: Uses robust subprocess management in Flask to prevent the web server from hanging during long-running data fetches.

📂 File Structure
The project maintains a clear separation between the web environment and the analytics engine, which is located in a dedicated subdirectory:

├── app.py                      # Flask Web Server (uses Gunicorn in production)
├── templates/
│   ├── index.html              # Landing page
│   └── dashboard.html          # Main application interface
├── .github/
│   └── actions/
│       └── action/             # The core analytics engine directory
│             ├── main.py            # Orchestrates data fetching and plotting
│             ├── github_api.py      # API communication utilities
│             ├── visualisation.py   # Plotting functions
│             ├── csv/               # Runtime storage for CSV output (temp files)
│             └── plots/             # Runtime storage for PNG plots (temp files)
├── Dockerfile                  # Container definition for production deployment
└── requirements.txt            # Python dependencies

🧠 How It Works
The application operates on a client-server-subprocess model:

 Client Request: The user clicks the "Run Analytics" button on the dashboard.html (Client).

 Server Execution (Gunicorn): An AJAX POST request is sent to the /run-analytics route in app.py (Flask Server, managed by Gunicorn).

 Subprocess Orchestration: app.py captures the necessary parameters (owner, repo, token) and executes main.py as a separate, time-limited Python process (subprocess.run).

 Data Generation: main.py fetches data, processes it using helper scripts, and writes all plots (.png) and CSVs to the runtime directories (/tmp/github_analytics/plots and /tmp/github_analytics/csv inside the container).

 Server Response: Once main.py successfully completes, Flask sends a JSON response back to the client (status: success).

 Data Display: The client-side JavaScript (dashboard.html) receives the success signal and triggers a refresh, fetching the newly generated files via the /plots/<filename> and /csv/<filename> routes.

⚙️ Prerequisites
Docker: Required for building and running the containerized application.

GitHub Personal Access Token (PAT): Required for authentication and bypassing rate limits.

🐍 Python Dependencies
The core application requires the following libraries, which are specified in requirements.txt:

Library

Purpose

Flask

Core web framework for the backend server (app.py).

requests

Used in github_api.py for making HTTP calls to the GitHub API.

pandas

Essential for data manipulation, cleaning, and analysis in main.py.

matplotlib

Base plotting library for creating visualizations.

seaborn

Visualization library built on Matplotlib for statistical plots.

gunicorn

Production WSGI HTTP Server used by the Docker container to serve Flask reliably.

🐳 Docker Deployment & Setup
This is the recommended way to run the application, especially for deployment on AWS.

 Clone the repository:
    bash     git clone [your-repo-link]     cd [your-repo-name]     

 Build the Docker image:
(Replace github-analytics with your preferred image name)
    bash     docker build -t github-analytics .     

 Run the container locally:
(The application will be accessible at http://localhost:8080)
    bash     docker run -d -p 8080:8080 --name analytics-app github-analytics     

Deployment to AWS
The built image is ready to be pushed to an AWS service:

Push to ECR: Tag and push your github-analytics image to your private Amazon ECR repository.

Deploy: Use the ECR image with services like AWS Fargate or AWS App Runner. These services will automatically use the gunicorn command defined in the Dockerfile.

🔑 Configuration
The application requires runtime configuration via URL parameters and input fields:

Repository Details
The dashboard requires the following input fields, which are passed to the backend via the client-side JavaScript:

Parameter

Location

Description

Owner

Input Field

The GitHub organization or user name (e.g., kubernetes).

Repo

Input Field

The repository name (e.g., kubernetes).

Token

Input Field

The user's GitHub Personal Access Token (PAT).

▶️ Usage
 Start the Application (Via Docker/Gunicorn):
    If running locally, follow the steps in the Docker Deployment section above.

 Generate Report:
    * Navigate to the running application (e.g., http://localhost:8080/dashboard).
    * Enter the Owner, Repo, and Token in the dashboard form.
    * Click Run Analytics.
    * Wait for the process to complete (max 120 seconds). The plots tab will activate automatically upon success.

 View Data:
    * Use the Plots tab to see visualizations.
    * Use the CSV Data tab to view and download raw data files.

📊 Output Format (Dashboard Display)
Once the analytics script completes successfully, the dashboard switches from the "Running..." status to displaying the results, organized into two main, clickable tabs:

1. Plots Tab (Visualizations)
This tab displays all the generated PNG image files fetched from the server's /plots/ endpoint.  
These visualizations provide immediate insight into repository activity and health:

Example Plot                  

Data Displayed                                                                

commit_activity.png        

Time series of commit volume over the selected period.                        

author_activity.png        

Breakdown of commits/contributions by individual authors.                      

time_to_merge.png          

Distribution (histogram) of the time taken for Pull Requests to be merged.    

reviewer_author_heatmap.png

Matrix showing interactions between reviewers and authors.                    

2. CSV Data Tab (Raw Data)
This tab displays links to the raw data files generated and saved to the  
.github/actions/action/csv/ directory. Users can interact with the raw data in two ways:

View Button: Opens a responsive modal pop-up that displays a preview of the CSV content  
  as a scrollable HTML table, ideal for quick inspection.

Download Button: Triggers a direct file download of the full CSV file (e.g., prs.csv, issues.csv)  
  to the user's local machine for further analysis in external tools.