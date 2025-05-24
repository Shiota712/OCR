
# DBを生成するためのプログラム
import sqlite3

DB_PATH = 'env/main/db/users.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ユーザーテーブル
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            balance INTEGER DEFAULT 0
        )
    ''')

    # アイテムテーブル（ユーザーにひもづく）
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            username TEXT,
            date TEXT,
            item_name TEXT,
            category TEXT,
            note TEXT,
            price INTEGER,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    ''')

    conn.commit()
    conn.close()

init_db()