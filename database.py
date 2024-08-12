import os
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name='database.db'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
        table_exists = c.fetchone()
        
        if not table_exists:
            c.execute('''CREATE TABLE sessions
                         (filename TEXT PRIMARY KEY, create_date TEXT, duration INTEGER, agent_name TEXT)''')
            print("Таблица 'sessions' создана.")
        else:
            print("Таблица 'sessions' уже существует.")
        
        conn.commit()
        conn.close()

    def save_session(self, filename, create_date, duration, agent_name):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?)",
                  (filename, create_date, duration, agent_name))
        conn.commit()
        conn.close()

    def get_recent_sessions(self, limit=10):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM sessions ORDER BY create_date DESC LIMIT ?", (limit,))
        sessions = c.fetchall()
        conn.close()
        return sessions

    def end_session(self, filename, end_time):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT create_date FROM sessions WHERE filename = ?", (filename,))
        result = c.fetchone()
        if result:
            start_time = datetime.fromisoformat(result[0])
            duration = (end_time - start_time).seconds
            c.execute("UPDATE sessions SET duration = ? WHERE filename = ?", (duration, filename))
            conn.commit()
        conn.close()

    def update_session_duration(self, filename):
        file_path = os.path.join("chats", filename)
        if os.path.exists(file_path):
            last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("SELECT create_date FROM sessions WHERE filename = ?", (filename,))
            result = c.fetchone()
            if result:
                start_time = datetime.fromisoformat(result[0])
                duration = int((last_modified - start_time).total_seconds())
                c.execute("UPDATE sessions SET duration = ? WHERE filename = ?", (duration, filename))
                conn.commit()
            conn.close()
        
    def get_session_duration(self, filename):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT duration FROM sessions WHERE filename = ?", (filename,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0