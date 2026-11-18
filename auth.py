import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import BASE_DIR, SESSION_TIMEOUT_MINUTES

USERS_FILE = os.path.join(BASE_DIR, 'users.json')
AUDIT_LOG_FILE = os.path.join(BASE_DIR, 'audit_log.json')

# Predefined accounts with secure password hashing
INITIAL_USERS = {
    'admin': {
        'username': 'admin',
        'full_name': 'Chief System Administrator',
        'role': 'Administrator',
        'password_hash': generate_password_hash('AdminSecure@2026')
    },
    'analyst': {
        'username': 'analyst',
        'full_name': 'Senior Crime Intelligence Analyst',
        'role': 'Analyst',
        'password_hash': generate_password_hash('AnalystPass@2026')
    },
    'officer': {
        'username': 'officer',
        'full_name': 'Field Operations Officer',
        'role': 'Police Officer',
        'password_hash': generate_password_hash('OfficerSafe@2026')
    },
    'decision_maker': {
        'username': 'decision_maker',
        'full_name': 'Strategic Command Commissioner',
        'role': 'Decision Maker',
        'password_hash': generate_password_hash('CommandLead@2026')
    }
}

def init_auth():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(INITIAL_USERS, f, indent=2)
            
    if not os.path.exists(AUDIT_LOG_FILE):
        initial_log = [
            {
                'id': 1,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'username': 'system',
                'role': 'System',
                'action': 'System Initialized',
                'details': 'Cognitive Digital Twin security and audit sub-system initialized.',
                'ip': '127.0.0.1',
                'status': 'SUCCESS'
            }
        ]
        with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_log, f, indent=2)

def get_users():
    init_auth()
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return INITIAL_USERS

def authenticate(username, password):
    users = get_users()
    user = users.get(username.strip().lower()) if username else None
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

def register_user(username, password, full_name, role='Analyst'):
    init_auth()
    users = get_users()
    clean_username = username.strip().lower()
    
    if not clean_username or len(clean_username) < 3:
        return False, "Username must be at least 3 characters long."
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if clean_username in users:
        return False, f"Username '{clean_username}' is already registered. Please choose another or sign in."
        
    valid_roles = ['Administrator', 'Analyst', 'Police Officer', 'Decision Maker']
    if role not in valid_roles:
        role = 'Analyst'
        
    new_user = {
        'username': clean_username,
        'full_name': full_name.strip() or clean_username.title(),
        'role': role,
        'password_hash': generate_password_hash(password)
    }
    users[clean_username] = new_user
    
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2)
        
    log_audit_action(clean_username, role, 'User Registration', f"New user '{clean_username}' registered with role '{role}'.")
    return True, new_user

def log_audit_action(username, role, action, details, status='SUCCESS', ip=None):
    init_auth()
    try:
        with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except Exception:
        logs = []
        
    entry = {
        'id': len(logs) + 1,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'username': username or 'anonymous',
        'role': role or 'Guest',
        'action': action,
        'details': details,
        'ip': ip or (request.remote_addr if request else '127.0.0.1'),
        'status': status
    }
    logs.insert(0, entry) # newest first
    # keep last 200 logs
    logs = logs[:200]
    with open(AUDIT_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)
    return entry

def get_audit_logs():
    init_auth()
    try:
        with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required', 'code': 'UNAUTHORIZED'}), 401
            return redirect(url_for('login_view', next=request.url))
            
        # Check session timeout
        last_active = session.get('last_active')
        if last_active:
            last_dt = datetime.fromisoformat(last_active)
            if datetime.now() - last_dt > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                session.clear()
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Session expired due to inactivity', 'code': 'SESSION_TIMEOUT'}), 401
                return redirect(url_for('login_view', message='Session expired due to inactivity. Please log in again.'))
                
        session['last_active'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            user_role = session['user'].get('role')
            if user_role not in allowed_roles and user_role != 'Administrator':
                return jsonify({'error': f'Access restricted. Requires one of: {", ".join(allowed_roles)}'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
