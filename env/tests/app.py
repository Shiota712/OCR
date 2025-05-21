from flask import Flask
from auth.routes import auth_bp  # ログイン関連
from receipts.routes import receipts_bp  # レシート関連

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # セッション用のキー

# Blueprint登録
app.register_blueprint(auth_bp)
app.register_blueprint(receipts_bp)

@app.route('/')
def home():
    return '<a href="/auth/login">ログインはこちら</a>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)