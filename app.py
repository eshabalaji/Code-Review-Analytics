from flask import Flask, render_template, request, session, jsonify, send_from_directory, redirect, url_for
import os
import subprocess
import sys
import uuid
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY','fallback-key')

logging.basicConfig(level=logging.INFO)

# Define main script path
ACTION_DIR = os.path.join(os.path.dirname(__file__), '.github', 'actions', 'action')
MAIN_SCRIPT_PATH = 'main.py'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process-input', methods=['POST'])
def process_input():
    owner = request.form.get('owner')
    repo = request.form.get('repo')
    token = request.form.get('token')

    # Generate unique temp folder for this session
    session_id = str(uuid.uuid4())
    temp_dir = os.path.join('/tmp', session_id)
    plots_dir = os.path.join(temp_dir, 'plots')
    csv_dir = os.path.join(temp_dir, 'csv')
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)

    # Store paths & token in session
    session['GITHUB_TOKEN'] = token
    session['TEMP_DIR'] = temp_dir
    session['PLOTS_DIR'] = plots_dir
    session['CSVS_DIR'] = csv_dir
    session['OWNER'] = owner
    session['REPO'] = repo

    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    # If session data missing, redirect home
    if not session.get('TEMP_DIR'):
        return redirect(url_for('home'))
    return render_template('dashboard.html')

@app.route('/run-analytics', methods=['POST'])
def run_analytics():
    token = session.get('GITHUB_TOKEN')
    owner = session.get('OWNER')
    repo = session.get('REPO')
    temp_dir = session.get('TEMP_DIR')

    if not all([owner, repo, temp_dir]):
        return jsonify({'status':'error','message':'Session expired or invalid.'})

    env = os.environ.copy()
    env['OWNER'] = owner
    env['REPO'] = repo
    env['PLOTS_DIR'] = session['PLOTS_DIR']
    env['CSVS_DIR'] = session['CSVS_DIR']
    if token:
        env['GITHUB_TOKEN'] = token

    try:
        result = subprocess.run(
            [sys.executable, MAIN_SCRIPT_PATH],
            cwd=ACTION_DIR,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=600
        )
        return jsonify({'status':'success','stdout':result.stdout,'stderr':result.stderr})
    except Exception as e:
        return jsonify({'status':'error','message': str(e)})

@app.route('/plots/<filename>')
def serve_plots(filename):
    plots_dir = session.get('PLOTS_DIR')
    if not plots_dir:
        return "Session expired", 404
    return send_from_directory(plots_dir, filename)

@app.route('/csv/<filename>')
def serve_csv(filename):
    csv_dir = session.get('CSVS_DIR')
    if not csv_dir:
        return "Session expired", 404
    return send_from_directory(csv_dir, filename, as_attachment=True)


if __name__ == '__main__':
    if ACTION_DIR not in sys.path:
        sys.path.append(ACTION_DIR)

    import os
    port = int(os.environ.get('PORT', 8080))  # Cloud Run uses port 8080
    app.run(host='0.0.0.0', port=port)
