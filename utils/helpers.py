import sqlite3
from datetime import datetime

DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    is_admin INTEGER DEFAULT 0
                )''')
    # Teams table
    c.execute('''CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )''')
    # Team members
    c.execute('''CREATE TABLE IF NOT EXISTS team_members (
                    team_id INTEGER,
                    user_id INTEGER,
                    FOREIGN KEY(team_id) REFERENCES teams(id),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    # Messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER,
                    receiver_id INTEGER,
                    team_id INTEGER,
                    message TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(sender_id) REFERENCES users(id),
                    FOREIGN KEY(receiver_id) REFERENCES users(id),
                    FOREIGN KEY(team_id) REFERENCES teams(id)
                )''')
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, args)
    rv = c.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv