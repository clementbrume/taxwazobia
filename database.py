import sqlite3

# Connect to (or create) a database file called metrics.db
def get_db_connection():
    conn = sqlite3.connect('metrics.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create the table if it doesn’t exist
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usage_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_count INTEGER DEFAULT 0
        );
    ''')
    conn.commit()
    conn.close()

# Add a new user (if not exists)
def add_user(chat_id):
    conn = get_db_connection()
    conn.execute('INSERT OR IGNORE INTO usage_metrics (chat_id) VALUES (?)', (chat_id,))
    conn.commit()
    conn.close()

# Increment error count for a user
def increment_error(chat_id):
    conn = get_db_connection()
    conn.execute('UPDATE usage_metrics SET error_count = error_count + 1 WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()

# Get total user count and total errors
def get_metrics():
    conn = get_db_connection()
    users = conn.execute('SELECT COUNT(*) FROM usage_metrics').fetchone()[0]
    errors = conn.execute('SELECT SUM(error_count) FROM usage_metrics').fetchone()[0]
    conn.close()
    return users, errors or 0
