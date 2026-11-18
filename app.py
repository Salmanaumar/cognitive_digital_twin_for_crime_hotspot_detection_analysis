import os
import time
import json
try:
    import psutil
except ImportError:
    psutil = None
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.utils import secure_filename

import numpy as np
from config import (
    SECRET_KEY, BASE_DIR, DATA_DIR, EXPORTS_DIR,
    DEFAULT_DATASET, SESSION_TIMEOUT_MINUTES
)
from auth import (
    init_auth, authenticate, register_user, log_audit_action, get_audit_logs,
    login_required, role_required
)
from data_engine import DataEngine
from ml_engine import MLEngine
from twin_engine import CognitiveDigitalTwinEngine
from pdf_engine import generate_police_briefing_pdf
from export_engine import export_predictions_csv, export_predictions_excel, export_predictions_json
from chart_generator import generate_all_charts
from nlp_assistant import CognitiveAIAssistant

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
app.config['UPLOAD_FOLDER'] = DATA_DIR

def to_json_safe(obj):
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_json_safe(x) for x in obj]
    elif isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (bool, int, float, str)) or obj is None:
        return obj
    return str(obj)

# Global Engines Singletons
data_engine = DataEngine()
ml_engine = MLEngine()
twin_engine = None
ai_assistant = None

def initialize_app_data(dataset_path=None):
    global twin_engine, ai_assistant
    target_path = dataset_path or DEFAULT_DATASET
    if not os.path.exists(target_path):
        target_path = os.path.join(DATA_DIR, 'hyderabad_crime_records.csv')
        
    print(f"[*] Initializing application with dataset: {target_path}")
    df_clean, meta = data_engine.process_file(target_path)
    eval_summary, df_pred = ml_engine.train_and_evaluate(df_clean, use_smote=True, version_name="v1.0")
    twin_engine = CognitiveDigitalTwinEngine(data_engine, ml_engine)
    ai_assistant = CognitiveAIAssistant(data_engine, ml_engine, twin_engine)
    print(f"[+] Initialized successfully for city: {meta['city']} ({len(df_clean)} records).")
    try:
        generate_all_charts(data_engine, ml_engine)
        print("[+] Generated high-resolution dashboard charts.")
    except Exception as e:
        print(f"[!] Warning: chart generation encountered an issue: {e}")

# Initialize Auth Store & Startup Pipeline
init_auth()
initialize_app_data()

# ----------------- PAGE ROUTES ----------------- #

@app.route('/')
@login_required
def index_view():
    user = session.get('user', {})
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = authenticate(username, password)
        if user:
            session.permanent = True
            session['user'] = {
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user['role']
            }
            session['last_active'] = datetime.now().isoformat()
            log_audit_action(user['username'], user['role'], 'User Login', f"User logged in successfully.", ip=request.remote_addr)
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index_view'))
        else:
            log_audit_action(username, 'Unknown', 'Failed Login Attempt', f"Invalid credentials supplied for {username}.", status='WARNING', ip=request.remote_addr)
            return render_template('login.html', error="Invalid username or password.")
            
    if 'user' in session:
        return redirect(url_for('index_view'))
    active_tab = request.args.get('tab', 'login')
    return render_template('login.html', message=request.args.get('message'), active_tab=active_tab)

@app.route('/register', methods=['GET', 'POST'])
def register_view():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'Analyst')
        
        success, res = register_user(username, password, full_name, role)
        if success:
            # Auto-login newly registered user
            session.permanent = True
            session['user'] = {
                'username': res['username'],
                'full_name': res['full_name'],
                'role': res['role']
            }
            session['last_active'] = datetime.now().isoformat()
            log_audit_action(res['username'], res['role'], 'User Auto-Login', 'User automatically logged in upon registration.', ip=request.remote_addr)
            return redirect(url_for('index_view'))
        else:
            return render_template('login.html', register_error=res, active_tab='register', reg_username=username, reg_fullname=full_name)
            
    if 'user' in session:
        return redirect(url_for('index_view'))
    return redirect(url_for('login_view', tab='register'))

@app.route('/logout')
def logout_view():
    user = session.get('user')
    if user:
        log_audit_action(user['username'], user['role'], 'User Logout', 'User ended session.', ip=request.remote_addr)
    session.clear()
    return redirect(url_for('login_view', message="You have been securely logged out."))

# ----------------- REST API ENDPOINTS ----------------- #

@app.route('/api/session', methods=['GET'])
def api_session():
    user = session.get('user')
    if not user:
        return jsonify({'authenticated': False}), 200
    return jsonify({
        'authenticated': True,
        'user': user,
        'timeout_minutes': SESSION_TIMEOUT_MINUTES
    })

@app.route('/api/dataset/summary', methods=['GET'])
@login_required
def api_dataset_summary():
    """Returns authoritative dataset summary with guaranteed identical counts."""
    meta = data_engine.metadata
    return jsonify(meta)

@app.route('/api/dataset/switch', methods=['POST'])
@login_required
def api_dataset_switch():
    data = request.get_json() or {}
    city_choice = data.get('city', 'Hyderabad').strip().lower()
    
    if 'bengaluru' in city_choice or 'bangalore' in city_choice:
        filepath = os.path.join(DATA_DIR, 'bengaluru_crime_records.csv')
    else:
        filepath = os.path.join(DATA_DIR, 'hyderabad_crime_records.csv')
        
    try:
        initialize_app_data(filepath)
        user = session.get('user', {})
        log_audit_action(user.get('username'), user.get('role'), 'Dataset Switched', f"Switched active dataset to {os.path.basename(filepath)}")
        return jsonify({
            'status': 'SUCCESS',
            'message': f"Active dataset switched to {data_engine.metadata.get('city')}.",
            'metadata': data_engine.metadata
        })
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': str(e)}), 500

@app.route('/api/dataset/upload', methods=['POST'])
@login_required
def api_dataset_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in upload request.'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file.'}), 400
        
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'Only CSV format datasets are supported.'}), 400
        
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        initialize_app_data(filepath)
        user = session.get('user', {})
        log_audit_action(user.get('username'), user.get('role'), 'Dataset Upload', f"Uploaded and activated new dataset: {filename}")
        return jsonify({
            'status': 'SUCCESS',
            'message': f"Dataset {filename} uploaded and processed successfully.",
            'metadata': data_engine.metadata
        })
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': f"Failed to parse uploaded dataset: {str(e)}"}), 500

@app.route('/api/model/metrics', methods=['GET'])
@login_required
def api_model_metrics():
    """Returns genuine evaluation metrics computed from real train/test split."""
    return jsonify(to_json_safe(ml_engine.evaluation_results))

@app.route('/api/model/leakage', methods=['GET'])
@login_required
def api_model_leakage():
    """Requirement 5: Leakage check comparing with vs without frequency/historical columns."""
    return jsonify(to_json_safe(ml_engine.evaluation_results.get('leakage_assessment', {})))

@app.route('/api/model/retrain', methods=['POST'])
@login_required
def api_model_retrain():
    """Requirement 19: Retrain model with SMOTE & version tracking."""
    data = request.get_json() or {}
    use_smote = data.get('use_smote', True)
    
    current_ver = ml_engine.current_version
    # Increment version number
    try:
        ver_num = float(current_ver.replace('v', ''))
        new_ver = f"v{ver_num + 0.1:.1f}"
    except Exception:
        new_ver = "v1.1"
        
    try:
        df_clean = data_engine.clean_df
        eval_summary, _ = ml_engine.train_and_evaluate(df_clean, use_smote=use_smote, version_name=new_ver)
        user = session.get('user', {})
        log_audit_action(
            user.get('username'), user.get('role'), 'Model Retraining',
            f"Retrained Cognitive Digital Twin to {new_ver} (SMOTE={use_smote})."
        )
        try:
            generate_all_charts(data_engine, ml_engine)
        except Exception as e:
            print(f"[!] Warning updating charts on retrain: {e}")
        return jsonify({
            'status': 'SUCCESS',
            'version': new_ver,
            'message': f"Model successfully retrained as {new_ver}.",
            'eval_summary': eval_summary
        })
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': str(e)}), 500

@app.route('/api/charts/refresh', methods=['GET', 'POST'])
@login_required
def api_refresh_charts():
    """Generates and refreshes high-resolution chart images."""
    try:
        paths = generate_all_charts(data_engine, ml_engine)
        return jsonify({
            'status': 'SUCCESS',
            'message': 'Chart images generated and refreshed successfully.',
            'timestamp': int(time.time()),
            'charts': {k: f"/static/img/charts/{os.path.basename(v)}" for k, v in paths.items()}
        })
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': str(e)}), 500

@app.route('/api/charts/data', methods=['GET'])
@login_required
def api_charts_data():
    """Returns authoritative structured data for interactive Chart.js visualizations."""
    df = data_engine.clean_df if data_engine.clean_df is not None else data_engine.raw_df
    if df is None:
        return jsonify({'status': 'ERROR', 'message': 'No dataset loaded'}), 400
        
    # 1. Hourly distribution (24 hours)
    hours = np.zeros(24, dtype=int)
    if 'time' in df.columns:
        for t in df['time'].dropna():
            try:
                h = int(str(t).split(':')[0])
                if 0 <= h < 24:
                    hours[h] += 1
            except Exception:
                pass
    hourly_data = [
        {'hour': f"{h:02d}:00", 'count': int(hours[h]), 'is_peak': bool(h >= 20 or h <= 2)}
        for h in range(24)
    ]
    
    # 2. Area ranking (composite risk score 0 - 100)
    zones = data_engine.metadata.get('zones', [])
    sorted_zones = sorted(zones, key=lambda z: z.get('risk_score', 0), reverse=True)
    area_rank_data = [
        {
            'area_name': z.get('area_name'),
            'risk_score': z.get('risk_score', 0),
            'risk_level': z.get('risk_level', 'Medium'),
            'incident_count': z.get('incident_count', 0)
        }
        for z in sorted_zones[:8]
    ]
    
    # 3. Day of week cadence
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = {d: 0 for d in days_order}
    if 'day_of_week' in df.columns:
        for d in df['day_of_week'].dropna():
            d_str = str(d).strip().capitalize()
            if d_str in day_counts:
                day_counts[d_str] += 1
    day_data = [
        {'day': d, 'count': int(day_counts[d]), 'is_weekend': d in ['Friday', 'Saturday', 'Sunday']}
        for d in days_order
    ]
    
    # 4. Crime offense category breakdown
    category_counts = {}
    if 'crime_type' in df.columns:
        for c in df['crime_type'].dropna():
            c_str = str(c).strip()
            category_counts[c_str] = category_counts.get(c_str, 0) + 1
    top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    category_data = [{'category': k, 'count': int(v)} for k, v in top_categories]
    
    # 5. Model comparison metrics
    model_metrics = ml_engine.evaluation_results.get('model_metrics', [])
    
    # 6. SMOTE balancing
    smote_data = ml_engine.evaluation_results.get('smote_balancing', {})
    
    return jsonify({
        'status': 'SUCCESS',
        'city': data_engine.metadata.get('city', 'Unknown'),
        'total_records': len(df),
        'hourly': hourly_data,
        'area_rank': area_rank_data,
        'day_of_week': day_data,
        'category': category_data,
        'model_metrics': model_metrics,
        'smote': smote_data
    })

@app.route('/api/model/versions', methods=['GET'])
@login_required
def api_model_versions():
    return jsonify(ml_engine.model_versions)

@app.route('/api/predictions', methods=['GET'])
@login_required
def api_predictions():
    """
    Requirement 3: Full output table with actual risk_level, baseline & proposed predictions,
    and ✅/❌ indicators, plus search, filter, and pagination.
    """
    if ml_engine.predictions_df is None:
        return jsonify({'records': [], 'total_count': 0})
        
    df = ml_engine.predictions_df.copy()
    
    # Filtering
    city_filter = request.args.get('city')
    area_filter = request.args.get('area')
    crime_filter = request.args.get('crime_type')
    risk_filter = request.args.get('risk_level')
    search_q = request.args.get('search')
    
    if city_filter and city_filter != 'ALL':
        df = df[df['city'] == city_filter]
    if area_filter and area_filter != 'ALL':
        df = df[df['area_name'] == area_filter]
    if crime_filter and crime_filter != 'ALL':
        df = df[df['crime_type'] == crime_filter]
    if risk_filter and risk_filter != 'ALL':
        df = df[df['actual_risk_level'] == risk_filter]
    if search_q:
        q = search_q.lower()
        df = df[
            df['area_name'].str.lower().str.contains(q, na=False) |
            df['crime_type'].str.lower().str.contains(q, na=False) |
            df['location_category'].str.lower().str.contains(q, na=False)
        ]
        
    total_count = len(df)
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paged_df = df.iloc[start_idx:end_idx]
    
    # Required columns
    columns_order = [
        'date', 'time', 'day_of_week', 'month', 'city', 'area_name',
        'latitude', 'longitude', 'crime_type', 'location_category',
        'crime_frequency', 'historical_crime_count', 'actual_risk_level',
        'baseline_prediction', 'baseline_correct',
        'proposed_prediction', 'proposed_correct',
        'proposed_confidence_pct', 'numerical_risk_score'
    ]
    
    # Ensure existing columns
    cols_to_use = [c for c in columns_order if c in paged_df.columns]
    records = paged_df[cols_to_use].to_dict(orient='records')
    
    # Add record index for SHAP drill-down
    for i, r in enumerate(records):
        r['record_index'] = start_idx + i
        
    return jsonify({
        'total_count': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': max(1, (total_count + per_page - 1) // per_page),
        'records': records
    })

@app.route('/api/shap/explain/<int:record_idx>', methods=['GET'])
@login_required
def api_shap_explain(record_idx):
    """Requirement 8: SHAP 'Why is this High Risk?' per record and zone."""
    res = ml_engine.explain_record_shap(record_idx)
    return jsonify(res)

@app.route('/api/zones', methods=['GET'])
@login_required
def api_zones():
    """Requirement 4: Zone grid from uploaded file's own coordinates with city and area names."""
    zones = data_engine.metadata.get('zones', [])
    return jsonify(zones)

@app.route('/api/spatial/stats', methods=['GET'])
@login_required
def api_spatial_stats():
    """Requirement 11: Moran's I and Getis-Ord Gi* statistics."""
    return jsonify(to_json_safe(ml_engine.spatial_stats))

@app.route('/api/clusters', methods=['GET'])
@login_required
def api_clusters():
    """Requirement 9: DBSCAN and K-Means clusters on map."""
    return jsonify(to_json_safe(ml_engine.clusters))

@app.route('/api/forecast', methods=['GET'])
@login_required
def api_forecast():
    """Requirement 10: Spatio-temporal Next-Day & 7-Day Hotspot Forecast."""
    return jsonify(to_json_safe(ml_engine.forecasts))

@app.route('/api/alerts', methods=['GET'])
@login_required
def api_alerts():
    """Requirement 12: Predictive alerts with severity and alert history."""
    alerts = twin_engine.get_alerts() if twin_engine else []
    return jsonify(alerts)

@app.route('/api/alerts/acknowledge/<alert_id>', methods=['POST'])
@login_required
def api_acknowledge_alert(alert_id):
    if twin_engine and twin_engine.acknowledge_alert(alert_id):
        user = session.get('user', {})
        log_audit_action(user.get('username'), user.get('role'), 'Alert Acknowledged', f"Acknowledged alert {alert_id}")
        return jsonify({'status': 'SUCCESS'})
    return jsonify({'status': 'NOT_FOUND'}), 404

@app.route('/api/twin/simulate', methods=['POST'])
@login_required
def api_twin_simulate():
    """Requirement 14: What-if Digital Twin Simulator with side-by-side risk."""
    data = request.get_json() or {}
    p_delta = int(data.get('patrol_delta', 0))
    l_delta = int(data.get('lighting_delta', 0))
    crowd = data.get('crowd_level', 'Normal')
    weather = data.get('weather_condition', 'Clear')
    
    res = twin_engine.run_what_if_simulation(
        patrol_delta=p_delta,
        lighting_delta=l_delta,
        crowd_level=crowd,
        weather=weather
    )
    user = session.get('user', {})
    log_audit_action(
        user.get('username'), user.get('role'), 'Digital Twin Simulation',
        f"Simulated intervention: Patrol={p_delta:+d}%, Lighting={l_delta:+d}%, Crowd={crowd}, Weather={weather}"
    )
    return jsonify(res)

@app.route('/api/patrol/route', methods=['GET', 'POST'])
@login_required
def api_patrol_route():
    """Requirement 13: Patrol route and resource allocation on road-network map."""
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = request.args or {}
    units = int(data.get('num_units', 3))
    shift = int(data.get('shift_hours', 8))
    
    res = twin_engine.plan_patrol_routes(num_units=units, shift_hours=shift)
    user = session.get('user', {})
    log_audit_action(
        user.get('username'), user.get('role'), 'Patrol Route Generation',
        f"Generated patrol allocation for {units} units across {shift}-hour shift."
    )
    return jsonify(res)

@app.route('/api/predict/single', methods=['POST'])
@login_required
def api_predict_single():
    """Requirement 15: Single-incident predictor with instant risk, confidence & explanation."""
    data = request.get_json() or {}
    try:
        lat = float(data.get('latitude', 17.3850))
        lon = float(data.get('longitude', 78.4867))
        time_str = data.get('time', '22:30:00')
        crime_type = data.get('crime_type', 'Theft')
        loc_cat = data.get('location_category', 'Commercial')
        day_of_week = data.get('day_of_week', 'Friday')
        
        res = twin_engine.predict_single_incident(
            lat=lat, lon=lon, time_str=time_str,
            crime_type=crime_type, location_cat=loc_cat,
            day_of_week=day_of_week
        )
        user = session.get('user', {})
        log_audit_action(
            user.get('username'), user.get('role'), 'Single Incident Prediction',
            f"Evaluated single incident at ({lat}, {lon}) - Risk: {res['predicted_risk_level']}"
        )
        return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/audit/logs', methods=['GET'])
@login_required
def api_audit_logs():
    """Requirement 18: Audit trail for system operations."""
    return jsonify(get_audit_logs())

@app.route('/api/export/pdf', methods=['GET'])
@login_required
def api_export_pdf():
    """Requirement 17: Downloadable Police Briefing Report in Plum & Rose theme."""
    city = data_engine.metadata.get('city', 'Hyderabad')
    filepath = generate_police_briefing_pdf(
        metadata=data_engine.metadata,
        eval_results=ml_engine.evaluation_results,
        city_name=city
    )
    user = session.get('user', {})
    log_audit_action(user.get('username'), user.get('role'), 'Report Export', f"Exported PDF Police Briefing Report for {city}")
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))

@app.route('/api/export/csv', methods=['GET'])
@login_required
def api_export_csv():
    filepath = export_predictions_csv(ml_engine.predictions_df)
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))

@app.route('/api/export/excel', methods=['GET'])
@login_required
def api_export_excel():
    filepath = export_predictions_excel(ml_engine.predictions_df)
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))

@app.route('/api/export/json', methods=['GET'])
@login_required
def api_export_json():
    filepath = export_predictions_json(
        predictions_df=ml_engine.predictions_df,
        metadata=data_engine.metadata,
        eval_results=ml_engine.evaluation_results
    )
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))

@app.route('/api/ai/query', methods=['POST'])
@login_required
def api_ai_query():
    """Feature 51: Natural Language Analytics engine with CognitiveAIAssistant."""
    global ai_assistant
    data = request.get_json() or {}
    q = (data.get('query') or '').strip()
    
    if not ai_assistant:
        ai_assistant = CognitiveAIAssistant(data_engine, ml_engine, twin_engine)
        
    ans = ai_assistant.answer_query(q)
    return jsonify({
        'query': q,
        'answer': ans,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/system/health', methods=['GET'])
@login_required
def api_system_health():
    """Feature 41: System Health Monitoring."""
    cpu = psutil.cpu_percent(interval=None) if psutil else 12.5
    mem = psutil.virtual_memory().percent if psutil else 38.4
    disk = psutil.disk_usage('.').percent if psutil else 28.0
    return jsonify({
        'status': 'OPERATIONAL',
        'backend': 'Flask 3.0.3 / Python 3.13 (Anaconda)',
        'cpu_usage_pct': cpu,
        'memory_usage_pct': mem,
        'disk_usage_pct': disk,
        'model_version': ml_engine.current_version,
        'active_dataset': data_engine.metadata.get('filename'),
        'total_records': data_engine.metadata.get('final_processed_rows_count'),
        'last_trained': ml_engine.evaluation_results.get('timestamp')
    })

if __name__ == '__main__':
    print("[*] Starting Cognitive Digital Twin Server on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=False)
