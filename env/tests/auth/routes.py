from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

DB_PATH = 'env/tests/db/users.db'

# ログイン機能　ユーザーの入力情報を取得して保存
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT password FROM users WHERE username = ?', (username,))     # ユーザーのpasswordを検索
        row = c.fetchone()

        if row:
            # ログイン
            if row[0] == password:
                session['username'] = username
                return redirect(url_for('auth.index'))
            else:
                flash('パスワードが違います')
        else:
            # 新規登録
            c.execute('INSERT OR REPLACE INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            session['username'] = username

            flash('新しいユーザーを登録しました')
            return redirect(url_for('auth.index'))
        
        conn.close()

    return render_template('login.html')

@auth_bp.route('/index')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('auth.login'))

