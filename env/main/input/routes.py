import base64
import json
import os
import re
import sqlite3
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from flask import Blueprint, jsonify, render_template, request, session
import google.generativeai as genai
import pytesseract

input_bp = Blueprint('input', __name__, url_prefix='/input')

# 環境変数の読み込み
load_dotenv()
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH')
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash-latest")
DB_PATH = os.getenv('DB_PATH')

# カテゴリ
category = ["食費","日用品","衣服","交際費","医療費","交通費","その他"]

@input_bp.route("/")
def input():
    username=session.get("username")
    return render_template('input.html', username=username)


# レシート画像のアップロードと解析
@input_bp.route('/upload', methods=['POST'])
def upload_receipt():
    data = request.get_json()

    if not data or 'image' not in data:
        return jsonify({'error': '画像データがありません'}), 400

    image_data = data['image']

    try:
        # base64デコードして画像として読み込む
        encoded = data['image'].split(",", 1)[1]
        image_binary = base64.b64decode(encoded.encode('utf-8'))
        image = Image.open(BytesIO(image_binary))

        # OCRでテキストを抽出
        ocr_text = extract_text_from_image(image)
        print("OCR\n", ocr_text)

        # Gemini APIで解析
        parsed_data = parse_receipt_with_gemini(ocr_text)
        print("解析結果：\n", parsed_data)

        return jsonify(parsed_data)

    except Exception as e:
        print("エラー:", e)
        return jsonify({'error': str(e)}), 500


# OCR処理（画像から日本語テキスト抽出）
def extract_text_from_image(image):
    # PIL → OpenCV
    image = np.array(image)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # NumPy配列 → PIL.Image に変換して表示
    pil_image = Image.fromarray(thresh)
    pil_image.show()  # OSの画像ビューアで表示される

    return pytesseract.image_to_string(thresh, lang="jpn")

# GeminiでOCR結果を解析し、項目ごとのJSONデータに変換
def parse_receipt_with_gemini(ocr_text):
    prompt = f"""
    Receipt textはレシートをOCRで解析したものです。このテキストから商品名と金額を抽出、または予測して、json形式で出力してください。# PIL → OpenCV
        image = np.array(pil_image)
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
        return Image.fromarray(thresh)
    
    # 画像を読み込み
    img = Image.open("example.jpg")
    
    # 前処理して表示
    processed_img = preprocess_image_for_ocr(img)
    processed_img.show()  # OSの画像ビューアで表示されます
    カテゴリはAvailable categoriesから選んでください。金額は"xx円","￥xx","xx※","xx軽"等のように表記されていることが多いです。
    フォーマットは次の通りです。

    Format:
    [
    {{
        "username": "{session.get('username')}",
        "item_name": "example product",
        "category": "predicted category",
        "note": "", //空白
        "price": 1234
    }},
    ...
    ]

    Available categories: {category}
    Receipt text: {ocr_text}

    意味のないな文字列（ノイズ）は全て省略してください。
    """
   
    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # JSON部分のみを抽出（囲み文字などを除去）
    cleaned_text = re.sub(r"^```json|```$", "", raw_text, flags=re.MULTILINE).strip()
    match = re.search(r'\[.*\]', cleaned_text, re.DOTALL)

    if match:
        json_part = match.group(0)
        return json.loads(json_part)
    else:
        raise ValueError("エラー:"+cleaned_text)


# フロントから送信された確定データをDBに保存
@input_bp.route('/submit', methods=['POST'])
def handle_submit():
    data = request.get_json()
    records = data.get('records', [])
    username = session.get('username')
    print("受け取ったデータ:", records)

    if not username:
        return jsonify({"status": "error", "message": "ユーザー未ログイン"}), 401

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 受け取ったデータをDBに挿入
    for item in records:
        c.execute('INSERT INTO items (username, date, item_name, category, note, price) VALUES (?, ?, ?, ?, ?, ?)', 
                  (username, item[0], item[1], item[2], item[3], int(item[4])))

    # 合計支出を計算
    total_expense = sum(int(item[4]) for item in records)

    # 現在の所持金(balance)を取得
    c.execute('SELECT balance FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    current_balance = row[0]
    if current_balance is None:
        current_balance = 0

    # 新しい残高を計算
    new_balance = current_balance - total_expense

    # ユーザーテーブルの残高を更新
    c.execute('UPDATE users SET balance = ? WHERE username = ?', (new_balance, username))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})
