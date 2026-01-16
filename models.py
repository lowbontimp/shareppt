import sqlite3
import os
from datetime import datetime, timedelta

DATABASE = '/home/hbim/share_ppts/files.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with File table"""
    conn = get_db()
    # Create table without password_hash (new structure)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            upload_time TIMESTAMP NOT NULL,
            file_path TEXT NOT NULL
        )
    ''')
    # Check if old table with password_hash exists and migrate
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(files)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'password_hash' in columns:
            # Old table structure exists, create new table and migrate
            conn.execute('''
                CREATE TABLE IF NOT EXISTS files_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    upload_time TIMESTAMP NOT NULL,
                    file_path TEXT NOT NULL
                )
            ''')
            conn.execute('''
                INSERT INTO files_new (id, filename, original_filename, upload_time, file_path)
                SELECT id, filename, original_filename, upload_time, file_path FROM files
            ''')
            conn.execute('DROP TABLE files')
            conn.execute('ALTER TABLE files_new RENAME TO files')
        cursor.close()
    except sqlite3.OperationalError:
        pass
    
    # Add uploader_email column if it doesn't exist
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(files)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'uploader_email' not in columns:
            conn.execute('ALTER TABLE files ADD COLUMN uploader_email TEXT')
            print("Added uploader_email column to files table")
        cursor.close()
    except sqlite3.OperationalError as e:
        print(f"Error adding uploader_email column: {e}")
    
    # Add file_size column if it doesn't exist
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(files)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'file_size' not in columns:
            conn.execute('ALTER TABLE files ADD COLUMN file_size INTEGER')
            print("Added file_size column to files table")
        cursor.close()
    except sqlite3.OperationalError as e:
        print(f"Error adding file_size column: {e}")
    
    conn.commit()
    conn.close()

def add_file(filename, original_filename, file_path, uploader_email=None, file_size=None):
    """Add a new file record to database"""
    conn = get_db()
    upload_time = datetime.now()
    
    # Get file size if not provided
    if file_size is None and os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO files (filename, original_filename, upload_time, file_path, uploader_email, file_size)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, original_filename, upload_time, file_path, uploader_email, file_size))
    
    conn.commit()
    file_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return file_id

def get_file(file_id):
    """Get file record by ID"""
    conn = get_db()
    row = conn.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
    conn.close()
    return row

def get_all_files():
    """Get all file records"""
    conn = get_db()
    rows = conn.execute('SELECT * FROM files ORDER BY upload_time DESC').fetchall()
    conn.close()
    return rows

# Note: calculate_days_remaining function removed - automatic deletion feature not implemented
# def calculate_days_remaining(upload_time_str, days=14):
#     """Calculate remaining days until automatic deletion"""
#     ...

def delete_file(file_id):
    """Delete file record from database"""
    conn = get_db()
    conn.execute('DELETE FROM files WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()

def get_old_files(days=14):
    """Get files older than specified days"""
    conn = get_db()
    cutoff_date = datetime.now() - timedelta(days=days)
    
    rows = conn.execute(
        'SELECT * FROM files WHERE upload_time < ?',
        (cutoff_date,)
    ).fetchall()
    conn.close()
    return rows

