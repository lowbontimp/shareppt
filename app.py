from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import RequestEntityTooLarge
import os
import secrets
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from models import init_db, add_file, get_file, get_all_files, delete_file

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB max file size
app.config['UPLOAD_FOLDER'] = '/home/hbim/share_ppts/uploads'

# Use fixed SECRET_KEY from environment or file, or generate once and store
SECRET_KEY_FILE = '/home/hbim/share_ppts/secret_key.txt'
if os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, 'r') as f:
        app.config['SECRET_KEY'] = f.read().strip()
else:
    # Generate new secret key and save it
    secret_key = secrets.token_hex(32)
    with open(SECRET_KEY_FILE, 'w') as f:
        f.write(secret_key)
    app.config['SECRET_KEY'] = secret_key

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # 30일 영구 세션

# Session cookie settings for subpath deployment
app.config['SESSION_COOKIE_PATH'] = '/share'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Automatically detect HTTPS from X-Forwarded-Proto header (set by nginx)
# SESSION_COOKIE_SECURE will be set dynamically based on request.is_secure
# Default to True if behind HTTPS proxy (nginx sets X-Forwarded-Proto)
app.config['SESSION_COOKIE_SECURE'] = True  # Will be enforced by nginx HTTPS

# Support for subpath deployment (/share)
class ReverseProxied:
    """WSGI middleware to handle reverse proxy with subpath"""
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]
        scheme = environ.get('HTTP_X_FORWARDED_PROTO', 'http')
        environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

app.wsgi_app = ReverseProxied(app.wsgi_app)

# CSRF Protection
csrf = CSRFProtect(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'  # Protect against session fixation

# Flask-Login cookie settings
login_manager.remember_cookie_duration = timedelta(days=30)
login_manager.remember_cookie_httponly = True
login_manager.remember_cookie_samesite = 'Lax'

@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access - return JSON for API requests, redirect for web requests"""
    if request.path.startswith('/upload') or request.path.startswith('/delete'):
        # API request - return JSON error
        return jsonify({'error': 'Authentication required', 'login_required': True}), 401
    # Web request - redirect to login
    return redirect(url_for('login'))

# Users dictionary: email -> password_hash (bcrypt)
USERS = {}

def load_users_from_file(filename='ids01.txt'):
    """Load users from ids01.txt file"""
    global USERS
    USERS = {}
    
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found. No users loaded.")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                # Split by whitespace: email password
                parts = line.split(None, 1)  # Split into max 2 parts
                if len(parts) != 2:
                    print(f"Warning: Invalid line format in {filename}: {line}")
                    continue
                
                email = parts[0].strip()
                password = parts[1].strip()
                
                if email and password:
                    # Store bcrypt hash directly (no SHA-256 intermediate step)
                    USERS[email] = generate_password_hash(password)
                    print(f"Loaded user: {email}")
    except Exception as e:
        print(f"Error loading users from {filename}: {e}")

# Load users on startup
load_users_from_file()

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    """Load user by email (user_id)"""
    if user_id in USERS:
        return User(user_id)
    return None

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
init_db()

def format_datetime(dt):
    """Format datetime to Korean format: YYYY년 MM월 DD일 HH시 MM분 SS초"""
    if isinstance(dt, str):
        # Try to parse string datetime
        try:
            formats = [
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
            ]
            for fmt in formats:
                try:
                    dt = datetime.strptime(dt, fmt)
                    break
                except ValueError:
                    continue
            if isinstance(dt, str):
                return dt  # Return as-is if parsing failed
        except Exception:
            return dt
    if isinstance(dt, datetime):
        return dt.strftime('%Y년 %m월 %d일 %H시 %M분 %S초')
    return str(dt)

def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes is None:
        return '알 수 없음'
    
    try:
        size_bytes = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    except (ValueError, TypeError):
        return '알 수 없음'

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    """Handle file size limit exceeded error"""
    return jsonify({
        'error': '파일 크기가 10GB를 초과합니다. 최대 10GB까지 업로드할 수 있습니다.',
        'max_size': '10GB'
    }), 413

@app.route('/favicon.ico')
def favicon():
    """Handle favicon request - serve SVG first, fallback to PNG"""
    # Try SVG first (modern browsers support SVG favicons)
    svg_path = os.path.join(app.static_folder, 'favicon.svg')
    if os.path.exists(svg_path):
        return send_file(svg_path, mimetype='image/svg+xml')
    # Fallback to PNG
    png_path = os.path.join(app.static_folder, 'favicon.png')
    if os.path.exists(png_path):
        return send_file(png_path, mimetype='image/png')
    return '', 204  # No content

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with simple password authentication"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')  # Plain text password
        
        # Check if user exists and verify password using bcrypt
        if username in USERS:
            stored_hash = USERS[username]
            if check_password_hash(stored_hash, password):
                user = User(username)
                login_user(user, remember=True)
                session.permanent = True
                return redirect(url_for('index'))
        
        # Login failed
        files = get_all_files()
        file_list = []
        for file_record in files:
            uploader_email = dict(file_record).get('uploader_email')
            file_size = dict(file_record).get('file_size')
            if file_size is None:
                file_path = file_record['file_path']
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
            file_list.append({
                'id': file_record['id'],
                'original_filename': file_record['original_filename'],
                'upload_time': format_datetime(file_record['upload_time']),
                'filename': file_record['filename'],
                'uploader_email': uploader_email,
                'file_size': format_file_size(file_size),
                'can_delete': False
            })
        return render_template('index.html', files=file_list, login_error='아이디 또는 비밀번호가 올바르지 않습니다.', is_logged_in=False, current_user_email=None, login_nonce=None)
    
    # GET request - redirect to index
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    """Main page showing file list"""
    try:
        files = get_all_files()
        file_list = []
        current_user_email = current_user.id if current_user.is_authenticated else None
        
        for file_record in files:
            uploader_email = dict(file_record).get('uploader_email')
            file_size = dict(file_record).get('file_size')
            # If file_size is not in DB, try to get it from disk
            if file_size is None:
                file_path = file_record['file_path']
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
            file_list.append({
                'id': file_record['id'],
                'original_filename': file_record['original_filename'],
                'upload_time': format_datetime(file_record['upload_time']),
                'filename': file_record['filename'],
                'uploader_email': uploader_email,
                'file_size': format_file_size(file_size),
                'can_delete': current_user.is_authenticated and uploader_email == current_user_email
            })
        return render_template('index.html', files=file_list, is_logged_in=current_user.is_authenticated, current_user_email=current_user_email)
    except Exception as e:
        return render_template('index.html', files=[], error=str(e), is_logged_in=current_user.is_authenticated, current_user_email=None)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate secure filename
        original_filename = secure_filename(file.filename)
        if not original_filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        file_ext = os.path.splitext(original_filename)[1]
        secure_name = secrets.token_urlsafe(16) + file_ext
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_name)
        
        # Save file
        try:
            file.save(file_path)
            # Get file size after saving
            file_size = os.path.getsize(file_path)
        except Exception as e:
            return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
        
        # Add to database
        try:
            uploader_email = current_user.id  # Get current logged-in user's email
            file_id = add_file(secure_name, original_filename, file_path, uploader_email, file_size)
        except Exception as e:
            # If database insert fails, try to remove the saved file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            return jsonify({'error': f'Failed to save file record: {str(e)}'}), 500
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'file_id': file_id
        })
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/download/<int:file_id>')
def download_file(file_id):
    """Download a file"""
    file_record = get_file(file_id)
    if not file_record:
        return jsonify({'error': 'File not found'}), 404
    
    file_path = file_record['file_path']
    if not os.path.exists(file_path):
        # File missing from disk, remove from database
        delete_file(file_id)
        return jsonify({'error': 'File not found on disk'}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file_record['original_filename']
    )

@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file_endpoint(file_id):
    """Delete a file"""
    file_record = get_file(file_id)
    if not file_record:
        return jsonify({'error': 'File not found'}), 404
    
    # Check ownership: only the uploader can delete
    uploader_email = dict(file_record).get('uploader_email')
    current_user_email = current_user.id
    
    # If uploader_email is NULL, file cannot be deleted (old files)
    if uploader_email is None:
        return jsonify({'error': 'This file cannot be deleted (no owner information)'}), 403
    
    # Check if current user is the owner
    if uploader_email != current_user_email:
        return jsonify({'error': 'You do not have permission to delete this file'}), 403
    
    # Delete physical file first
    file_path = file_record['file_path']
    file_deleted = False
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            file_deleted = True
        except Exception as e:
            return jsonify({'error': f'Error deleting file: {str(e)}'}), 500
    
    # Only delete database record if physical file was successfully deleted
    if file_deleted:
        try:
            delete_file(file_id)
        except Exception as e:
            # If DB deletion fails but file is deleted, log error but return success
            # (file is already gone, can't rollback)
            print(f"Warning: File deleted but database record deletion failed: {e}")
    
    return jsonify({'success': True, 'message': 'File deleted successfully'})

if __name__ == '__main__':
    # Only enable debug mode in development
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)

