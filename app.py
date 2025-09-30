from flask import Flask, render_template, request, jsonify, send_from_directory
import subprocess
import os
import sys
import logging
from subprocess import TimeoutExpired # Import TimeoutExpired for specific error handling

# Define the full path to the 'action' directory, which contains main.py
ACTION_DIR = os.path.join(os.path.dirname(__file__), '.github', 'actions', 'action')
MAIN_SCRIPT_PATH = 'main.py' # Relative path used inside the subprocess call

app = Flask(__name__,
             static_folder='static',
             template_folder='templates')

# Configure logging to show info messages
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    """Serves the main input page."""
    return render_template('index.html')

@app.route('/Code-Review-Analytics')
def dashboard():
    """Serves the dashboard page."""
    return render_template('dashboard.html')

@app.route('/run-analytics', methods=['POST'])
def run_analytics():
    """Triggers the Python script to run the analytics and generate plots."""
    
    # Define the maximum time the script is allowed to run
    MAX_RUN_TIME = 120 # 120 seconds (2 minutes)

    env = os.environ.copy()
    env['GITHUB_TOKEN'] = request.form.get('token')
    env['OWNER'] = request.form.get('owner')
    env['REPO'] = request.form.get('repo')
    
    # Clean up empty environment variables (important for clean subprocess environments)
    if not env.get('GITHUB_TOKEN'):
        if 'GITHUB_TOKEN' in env: del env['GITHUB_TOKEN']
    if not env.get('OWNER'):
        if 'OWNER' in env: del env['OWNER']
    if not env.get('REPO'):
        if 'REPO' in env: del env['REPO']

    # Log the command being executed for debugging
    logging.info(f"Running analytics for {env.get('OWNER')}/{env.get('REPO')} with timeout={MAX_RUN_TIME}s")

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

        if result.returncode == 0:
            logging.info("Analytics script completed successfully.")
            return jsonify({
                'status': 'success',
                'message': 'Analytics run completed successfully.',
                'output': result.stdout,
                'error_output': result.stderr
            })
        else:
            logging.error(f"Analytics script failed with return code {result.returncode}.")
            logging.error(f"STDOUT: {result.stdout}")
            logging.error(f"STDERR: {result.stderr}")
            
            return jsonify({
                'status': 'error',
                'message': 'Analytics script failed. Check server logs for details.',
                'output': result.stdout,
                'error_output': result.stderr
            })

    except TimeoutExpired:
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
    plots_dir = os.path.join(ACTION_DIR, 'plots')
    return send_from_directory(plots_dir, filename)

@app.route('/csv/<path:filename>')
def serve_csvs(filename):
    """Serves the generated CSV files from the action's 'csv' subdirectory."""
    csvs_dir = os.path.join(ACTION_DIR, 'csv') 
    # as_attachment=True is generally good practice for serving data files.
    return send_from_directory(csvs_dir, filename, as_attachment=True)

if __name__ == '__main__':
    # Adding ACTION_DIR to sys.path is often done in complex environments,
    # but the subprocess call relies on 'cwd' and 'sys.executable' for correct execution.
    if ACTION_DIR not in sys.path:
        sys.path.append(ACTION_DIR)
        
    app.run(debug=True, port=5000)