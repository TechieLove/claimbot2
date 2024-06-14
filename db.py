import os
import random
import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect('cookies.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cookies (
            id INTEGER PRIMARY KEY,
            giftcode TEXT UNIQUE,
            cookie_file TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS redeemed (
            user_id INTEGER,
            giftcode TEXT,
            claim_time TIMESTAMP,
            UNIQUE(user_id, giftcode)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS giftcodes (
            user_id INTEGER,
            giftcode TEXT UNIQUE,
            generate_time TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

def can_claim_cookie(user_id):
    conn = sqlite3.connect('cookies.db')
    c = conn.cursor()
    c.execute('SELECT MAX(claim_time) FROM redeemed WHERE user_id=?', (user_id,))
    last_claim_time = c.fetchone()[0]
    conn.close()
    if last_claim_time:
        last_claim_time = datetime.strptime(last_claim_time, '%Y-%m-%d %H:%M:%S')
        return datetime.now() - last_claim_time >= timedelta(hours=3)
    else:
        return True

def can_generate_giftcode(user_id):
    conn = sqlite3.connect('cookies.db')
    c = conn.cursor()
    c.execute('SELECT MAX(generate_time) FROM giftcodes WHERE user_id=?', (user_id,))
    last_generate_time = c.fetchone()[0]
    conn.close()
    if last_generate_time:
        last_generate_time = datetime.strptime(last_generate_time, '%Y-%m-%d %H:%M:%S')
        return datetime.now() - last_generate_time >= timedelta(hours=6)
    else:
        return True

def is_valid_giftcode(giftcode):
    conn = sqlite3.connect('cookies.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM giftcodes WHERE giftcode=?', (giftcode,))
    valid = c.fetchone() is not None
    conn.close()
    return valid

def get_random_cookie_file():
    cookie_files = os.listdir('bulk_cookies')
    if cookie_files:
        return os.path.join('bulk_cookies', random.choice(cookie_files))
    else:
        return None

def redeem_giftcode(user_id, giftcode):
    conn = sqlite3.connect('cookies.db')
    c = conn.cursor()
    c.execute('INSERT INTO redeemed (user_id, giftcode, claim_time) VALUES (?, ?, ?)', (user_id, giftcode, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def add_giftcode(user_id, giftcode):
    conn = sqlite3.connect('cookies.db')
    c = conn.cursor()
    c.execute('INSERT INTO giftcodes (user_id, giftcode, generate_time) VALUES (?, ?, ?)', (user_id, giftcode, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def add_bulk_cookies(cookies):
    conn = sqlite3.connect('cookies.db')
    c = conn.cursor()
    for code, file_path in cookies:
        c.execute('INSERT OR REPLACE INTO cookies (giftcode, cookie_file) VALUES (?, ?)', (code, file_path))
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('cookies.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('cookies.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]
