from flask import Flask, redirect, session
from login.routes import login_bp
from input.routes import input_bp 
from record.routes import record_bp 

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Blueprint登録
app.register_blueprint(login_bp)
app.register_blueprint(input_bp)
app.register_blueprint(record_bp)

# アプリを起動時の処理
@app.route('/')
def login():
    return redirect('/login/challenge') 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)