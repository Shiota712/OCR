from flask import Blueprint, render_template, session, jsonify
import sqlite3
import os
from dotenv import load_dotenv

record_bp = Blueprint('record', __name__, url_prefix='/record')

load_dotenv()
DB_PATH = os.getenv('DB_PATH')

@record_bp.route("/")
def record():
    username = session.get("username")
    return render_template('record.html', username=username)

# ユーザーデータの取得
@record_bp.route('/getJson', methods=['GET'])
def get_logs():

    try:
        # SQLiteデータベースに接続し、現在のユーザーの記録を取得する
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            'SELECT date, item_name, category, note, price FROM items WHERE username = ?',
            (session['username'],)
        )
        rows = c.fetchall()
    except Exception as e:
        return jsonify({'error': 'DBエラー: ' + str(e)}), 500
    finally:
        conn.close()

    # 取得したデータをJSON形式に変換する
    logs = [
        {'date': r[0], 'item_name': r[1], 'category': r[2], 'note': r[3], 'price': r[4]}
        for r in rows
    ]

    return jsonify(logs)

# 残高を取得
@record_bp.route('/balance', methods=['GET'])
def get_balance():
    username = session.get('username')
    if not username:
        return jsonify({"status": "error", "message": "未ログイン"}), 401

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT balance FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()

    return jsonify({"status": "ok", "balance": row[0] or 0})
