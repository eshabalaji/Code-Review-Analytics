import os
import subprocess
import sys
import logging
import json # ADDED: Required for parsing structured output
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session

# Define the full path to the 'action' directory, which contains main.py
ACTION_DIR = os.path.join(os.path.dirname(__file__), '.github', 'actions', 'action')
MAIN_SCRIPT_PATH = 'main.py' # Relative path used inside the subprocess call

# Define the explicit paths for serving files
PLOTS_DIR = os.path.join(ACTION_DIR, 'plots')
CSVS_DIR = os.path.join(ACTION_DIR, 'csv')

app = Flask(__name__,
             static_folder='static',
             template_folder='templates')

# CRITICAL SECURITY STEP: Set a strong, random secret key for session management.
# This is mandatory for using Flask sessions to store the token securely.
app.secret_key = 'A_VERY_LONG_AND_SECURE_RANDOM_SECRET_KEY_FOR_FLASK_SESSIONS' 

# Configure logging to show info messages
logging.basicConfig(level=logging.INFO)

# Ensure output directories exist (will create the nested paths if they don't exist)
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(CSVS_DIR, exist_ok=True)

def extract_repo_info(stdout):
    """Parses structured repo information from the script's stdout."""
    start_tag = "---REPO-INFO-START---\n"
    end_tag = "---REPO-INFO-END---"

    start_index = stdout.find(start_tag)
    end_index = stdout.find(end_tag, start_index + len(start_tag))

    if start_index != -1 and end_index != -1:
        # Extract the JSON string between the markers
        json_str = stdout[start_index + len(start_tag):end_index].strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode repo info JSON: {e}")
            return None
    return None

@app.route('/')
def home():
    """Serves the main input page."""
    return render_template('index.html')

# ADDED SECURE TOKEN HANDLING ROUTE
@app.route('/process-input', methods=['POST'])
def process_input():
    """
    Handles the form submission (POST). 
    Stores the sensitive token in the session and redirects to the dashboard
    using only non-sensitive parameters in the URL.
    """
    owner = request.form.get('owner')
    repo = request.form.get('repo')
    token = request.form.get('token')
    
    # Store the token securely in the server-side session
    if token:
        session['GITHUB_TOKEN'] = token
        logging.info("GitHub Token successfully stored in session.")
    else:
        # Clear any old token if a user submits without one (e.g., public repo)
        session.pop('GITHUB_TOKEN', None) 
        logging.warning("No GitHub Token provided, checking for public access.")
        
    # Redirect to the dashboard using only non-sensitive GET parameters
    return redirect(url_for('dashboard', owner=owner, repo=repo))


@app.route('/dashboard') # Route updated to handle owner/repo in query args
def dashboard():
    """Serves the dashboard page."""
    owner = request.args.get('owner')
    repo = request.args.get('repo')

    # If essential parameters are missing (e.g., direct navigation), redirect home
    if not owner or not repo:
        return redirect(url_for('home'))
        
    return render_template('dashboard.html')

@app.route('/run-analytics', methods=['POST'])
def run_analytics():
    """Triggers the Python script to run the analytics and generate plots."""
    
    # Define the maximum time the script is allowed to run
    MAX_RUN_TIME = 600 # 10 minutes 

    # --- TOKEN FIX: Retrieve token securely from session ---
    token = session.get('GITHUB_TOKEN')
    
    # Retrieve owner/repo from POST body (sent by JavaScript)
    owner = request.form.get('owner')
    repo = request.form.get('repo')

    env = os.environ.copy()
    env['OWNER'] = owner
    env['REPO'] = repo
    
    # Only set GITHUB_TOKEN if it was provided and stored in the session
    if token:
        env['GITHUB_TOKEN'] = token
    else:
        env.pop('GITHUB_TOKEN', None)

    # Log the command being executed for debugging
    logging.info(f"Running analytics for {owner}/{repo} with timeout={MAX_RUN_TIME}s")

    try:
        # Run the subprocess with the crucial 'cwd' and 'timeout' parameters
        result = subprocess.run(
            [sys.executable, MAIN_SCRIPT_PATH], # Note: MAIN_SCRIPT_PATH is relative here because of cwd
            cwd=ACTION_DIR, # CRITICAL: Sets the working directory for main.py
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=MAX_RUN_TIME # CRITICAL: Prevents server hang
        )

        # --- New: Extract structured repo info from stdout ---
        repo_info = extract_repo_info(result.stdout)
        # ---------------------------------------------------

        if result.returncode == 0:
            logging.info("Analytics script completed successfully.")
            return jsonify({
                'status': 'success',
                'message': 'Analytics run completed successfully.',
                'output': result.stdout,
                'error_output': result.stderr,
                'repo_info': repo_info # Include structured data
            })
        else:
            logging.error(f"Analytics script failed with return code {result.returncode}.")
            logging.error(f"STDOUT: {result.stdout}")
            logging.error(f"STDERR: {result.stderr}")
            
            return jsonify({
                'status': 'error',
                'message': 'Analytics script failed. Check server logs for details.',
                'output': result.stdout,
                'error_output': result.stderr,
                'repo_info': repo_info # Also include info on failure if available
            })

    except subprocess.TimeoutExpired:
        # Handle the specific case where the script runs longer than MAX_RUN_TIME
        logging.error(f"Analytics script timed out after {MAX_RUN_TIME} seconds.")
        return jsonify({
            'status': 'error', 
            'message': f"Script timed out after {MAX_RUN_TIME} seconds. It may be processing a very large repository.",
            'output': '', 
            'error_output': f"Script execution exceeded timeout limit of {MAX_RUN_TIME} seconds."
        })
    
    except Exception as e:
        logging.exception("An exception occurred while running analytics.")
        return jsonify({'status': 'error', 'message': str(e), 'output': '', 'error_output': ''})

@app.route('/plots/<path:filename>')
def serve_plots(filename):
    """Serves the generated plot images from the action's 'plots' subdirectory."""
    # Uses the previously defined PLOTS_DIR
    return send_from_directory(PLOTS_DIR, filename)

@app.route('/csv/<path:filename>') # ADJUSTED ROUTE from '/csvs/' to '/csv/'
def serve_csvs(filename):
    """Serves the generated CSV files from the action's 'csv' subdirectory."""
    # Uses the previously defined CSVS_DIR
    return send_from_directory(CSVS_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    # Adding ACTION_DIR to sys.path is often done in complex environments,
    # but the subprocess call relies on 'cwd' and 'sys.executable' for correct execution.
    if ACTION_DIR not in sys.path:
        sys.path.append(ACTION_DIR)
        
    app.run(debug=True, port=5000)
