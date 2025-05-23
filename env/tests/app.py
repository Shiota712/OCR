from flask import Flask, redirect
from auth.routes import auth_bp
from receipts.routes import receipts_bp 

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # セッション用のキー

# Blueprint登録
app.register_blueprint(auth_bp)
app.register_blueprint(receipts_bp)

@app.route('/')
def home():
    return redirect('/auth/login') 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)