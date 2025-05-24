from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

login_bp = Blueprint('login', __name__, url_prefix='/login')

load_dotenv()
DB_PATH = os.getenv('DB_PATH')

# --------------------------------------------
# ユーザーログイン & 新規登録処理
# --------------------------------------------
@login_bp.route('/challenge', methods=['GET', 'POST'])
def challenge():
    if request.method == 'POST':
        # フォームからユーザー名とパスワードを取得
        username = request.form['username']
        password = request.form['password']

        # データベースに接続
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()

            # 入力されたユーザー名がすでに登録されているか確認
            c.execute('SELECT password FROM users WHERE username = ?', (username,))
            row = c.fetchone()

            if row:
                # 既存ユーザー ⇒ 入力パスワードとハッシュを照合
                if check_password_hash(row[0], password):
                    session['username'] = username
                    return redirect(url_for('login.dashboard'))
                else:
                    flash('パスワードが違います')
            else:
                # 新規ユーザー ⇒ ハッシュ化して登録
                hashed_password = generate_password_hash(password)
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
                conn.commit()

                session['username'] = username
                flash('新しいユーザーを登録しました')
                return redirect(url_for('login.dashboard'))

    # GETアクセス時はログインフォームを表示
    return render_template('login.html')

# --------------------------------------------
# ログイン後の画面表示（ユーザーがログインしていれば）
# --------------------------------------------
@login_bp.route('/dashboard')
def dashboard():
    # セッションにユーザー名がある ⇒ ログイン済み
    if 'username' in session:
        session.permanent = True
        return render_template('input.html', username=session['username'])

    # 未ログイン ⇒ ログインページにリダイレクト
    return redirect(url_for('login.challenge'))
