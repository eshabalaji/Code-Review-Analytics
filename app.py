import os
import subprocess
import json
import shutil
import atexit
import time
import tempfile
import logging
from flask import Flask, render_template, request, send_from_directory, abort, jsonify

# Setup logging
def setup_logging():
    """Configures the application's logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    global logger
    logger = logging.getLogger(__name__)

setup_logging()

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)


# Define consistent temporary directory paths
TEMP_ROOT = os.path.join(tempfile.gettempdir(), 'github_analytics')
PLOTS_DIR = os.path.join(TEMP_ROOT, 'plots')
CSVS_DIR = os.path.join(TEMP_ROOT, 'csv')

# Path to the analysis script in your repo
ACTION_MAIN_PATH = os.path.join(app.root_path, '.github', 'actions', 'action', 'main.py')

# ensure dirs exist
def ensure_dirs():
    """Ensure temp directories exist with proper permissions"""
    try:
        for directory in [PLOTS_DIR, CSVS_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory, mode=0o755, exist_ok=True)
            if not os.access(directory, os.W_OK):
                logger.error(f"Directory not writable: {directory}")
                raise PermissionError(f"Directory not writable: {directory}")
        logger.info(f"Temp directories created successfully at {TEMP_ROOT}")
    except Exception as e:
        logger.error(f"Failed to create temp directories: {str(e)}")
        raise


def clear_temp_dirs():
    """Clear temp directories before a run to avoid mixing artifacts."""
    try:
        if os.path.exists(TEMP_ROOT):
            shutil.rmtree(TEMP_ROOT)
    except Exception as e:
        app.logger.warning(f"Failed to remove temp root: {e}")
    # recreate
    ensure_dirs()

# register cleanup at exit
def cleanup_on_exit():
    try:
        if os.path.exists(TEMP_ROOT):
            shutil.rmtree(TEMP_ROOT)
            app.logger.info("Cleaned up temp folders at shutdown.")
    except Exception as e:
        app.logger.warning(f"Cleanup at exit failed: {e}")

atexit.register(cleanup_on_exit)


def run_analysis(owner, repo_name, user_token):
    """
    Runs the action/main.py script as a subprocess.
    """
    clear_temp_dirs() # start fresh for each invocation
    logger.info(f"Starting analysis for {owner}/{repo_name}")

    env = os.environ.copy()
    env['OWNER'] = owner
    env['REPO'] = repo_name
    if user_token:
        env['GITHUB_TOKEN'] = user_token

    if not os.path.exists(ACTION_MAIN_PATH):
        logger.error(f"Analysis script not found at {ACTION_MAIN_PATH}")
        return {
            'status': 'error',
            'message': f"Analysis script not found at {ACTION_MAIN_PATH}",
            'stdout': '',
            'stderr': ''
        }

    try:
        # Use python from the current environment
        result = subprocess.run(
            ['python', ACTION_MAIN_PATH],
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=300
        )

        stdout_output = result.stdout or ""
        stderr_output = result.stderr or ""
        logger.debug(f"Script stdout: \n{stdout_output}")
        logger.debug(f"Script stderr: \n{stderr_output}")


        if result.returncode != 0:
            logger.error(f"Script exited with code {result.returncode}")
            return {
                'status': 'error',
                'message': f"Script failed (exit code {result.returncode}). Check logs for details.",
                'stdout': stdout_output,
                'stderr': stderr_output,
                'plots': [],
                'csvs': []
            }

        # Expect structured JSON markers in stdout
        start_tag = "---REPO-INFO-START---"
        end_tag = "---REPO-INFO-END---"
        repo_info = {}
        if start_tag in stdout_output and end_tag in stdout_output:
            try:
                json_str = stdout_output.split(start_tag)[1].split(end_tag)[0].strip()
                repo_info = json.loads(json_str)
            except json.JSONDecodeError:
                logger.error('Failed to parse JSON from script output.')
                # Continue execution to try and list files, but set status to error

        # list artifacts in temp dirs (Crucial part: relies on main.py writing to PLOTS_DIR/CSVS_DIR)
        plots = [f for f in os.listdir(PLOTS_DIR) if f.lower().endswith('.png')]
        csvs = [f for f in os.listdir(CSVS_DIR) if f.lower().endswith('.csv')]
        logger.info(f"Analysis successful. Found {len(plots)} plots and {len(csvs)} CSVs.")

        return {
            'status': 'success',
            'message': f'Analysis completed for {owner}/{repo_name}',
            'repo_info': repo_info,
            'plots': plots,
            'csvs': csvs,
            'stdout': stdout_output,
            'stderr': stderr_output
        }

    except subprocess.TimeoutExpired:
        logger.error('Analysis timed out.')
        return { 'status': 'error', 'message': 'Analysis timed out.', 'stdout': '', 'stderr': '' }
    except Exception as e:
        logger.error(f'Unexpected server error during run_analysis: {str(e)}', exc_info=True)
        return { 'status': 'error', 'message': f'Unexpected server error: {str(e)}', 'stdout': '', 'stderr': '' }


# --- Routes ---

@app.route('/', methods=['GET'])
def dashboard():
    return render_template('dashboard.html')


@app.route('/run-analytics', methods=['POST'])
def run_analytics_route():
    """
    Handles JSON data for owner, repo, and token.
    """
    try:
        if not request.is_json:
            logger.warning('Request must be JSON')
            # Changed to return a custom error JSON instead of aborting
            return jsonify({
                'status': 'error', 
                'message': 'Request must be JSON.',
                'plots': [],
                'csvs': []
            }), 400
            
        data = request.get_json()
        
        owner = data.get('owner')
        repo = data.get('repo')
        token = data.get('token')

        if not owner or not repo:
            logger.warning(f"Missing owner or repo in request data: {data}")
            return jsonify({
                'status': 'error',
                'message': 'Owner and repo are required.',
                'plots': [],
                'csvs': []
            }), 400

        result = run_analysis(owner, repo, token)
        status_code = 200 if result.get('status') == 'success' else 400
        
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error in /run-analytics route: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal Server Error: {str(e)}', 'status': 'error'}), 500


@app.route('/plots/<path:filename>')
def serve_plot(filename):
    """Serves generated plots from the temporary plots directory."""
    try:
        logger.debug(f"Attempting to serve plot: {filename} from {PLOTS_DIR}")
        if '..' in filename or filename.startswith('/'):
            logger.warning(f"Invalid plot filename requested: {filename}")
            abort(404)
        
        return send_from_directory(PLOTS_DIR, filename)
    except FileNotFoundError:
        logger.error(f"Plot file not found: {filename} in {PLOTS_DIR}")
        abort(404)
    except Exception:
        abort(500)


@app.route('/csv/<path:filename>')
def serve_csv(filename):
    """Serves generated CSVs from the temporary csv directory."""
    try:
        logger.debug(f"Attempting to serve CSV: {filename} from {CSVS_DIR}")
        if '..' in filename or filename.startswith('/'):
            logger.warning(f"Invalid CSV filename requested: {filename}")
            abort(404)
        # as_attachment=True forces a download dialog in the browser
        return send_from_directory(CSVS_DIR, filename, as_attachment=True, mimetype='text/csv')
    except FileNotFoundError:
        logger.error(f"CSV file not found: {filename} in {CSVS_DIR}")
        abort(404)
    except Exception:
        abort(500)


# simple healthcheck
@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({'status': 'ok', 'time': int(time.time())})


# --- Error Handling Middleware ---

@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 Error: {e.description}")
    return jsonify({'error': 'Resource not found', 'message': e.description}), 404

@app.errorhandler(400)
def bad_request(e):
    logger.warning(f"400 Error: {e.description}")
    return jsonify({'error': 'Bad request', 'message': e.description}), 400

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 Internal Server Error: {e.description}", exc_info=True)
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred.'}), 500


if __name__ == '__main__':
    try:
        ensure_dirs()
    except Exception as e:
        logger.critical(f"FATAL: Could not initialize temp directories. Exiting. Error: {e}")
        exit(1)

    # Use 0.0.0.0 for hostability in containers/servers
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)