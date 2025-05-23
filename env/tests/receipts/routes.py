from flask import Flask, Blueprint, render_template, request, jsonify, session
import base64
import os
import re
import json
from io import BytesIO
from PIL import Image
import pytesseract
from dotenv import load_dotenv  # 環境変数の読み込み
import google.generativeai as genai
import sqlite3

receipts_bp = Blueprint('receipts', __name__, url_prefix='/receipts')

DB_PATH = 'env/tests/db/users.db'

load_dotenv()
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH')
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# カテゴリ
category = ["食費","日用品","衣服","交際費","医療費","交通費","その他"]

@receipts_bp.route('/receipts')
def jumpToIndex():
    return render_template('index.html')

@receipts_bp.route('/session-user')
def session_user():
    username = session.get('username')
    if username:
        return jsonify({'username': username})
    else:
        return jsonify({'username': None}), 401

# レシート読み取り
@receipts_bp.route('/upload', methods=['POST'])
def upload_receipt():
    data = request.get_json()

    if not data or 'image' not in data:
        return jsonify({'error': '画像データがありません'}), 400

    image_data = data['image']

    try:
        # base64デコード
        encoded = image_data.split(",", 1)[1]
        image_binary = base64.b64decode(encoded.encode('utf-8'))
        image = Image.open(BytesIO(image_binary))

        # 画像解析
        ocr_text = extract_text_from_image(image)
        parsed_data = parse_receipt_with_gemini(ocr_text)
        print("解析結果：\n", parsed_data)

        return jsonify(parsed_data)

    except Exception as e:
        print("エラー:", e)
        return jsonify({'error': str(e)}), 500


# 画像処理
def extract_text_from_image(image):
    #gray = cv2.cvtColor(image, cv2.COLORBGR2GRAY)
    #gray = cv2.medianBlur(gray, 3)
    #thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY   cv2.THRESH_OTSU)

    return pytesseract.image_to_string(image, lang="jpn")

# Geminiに解析依頼
def parse_receipt_with_gemini(ocr_text):
    prompt = f"""
    From the following receipt text, extract the product names and prices, and format them as a JSON list.
    Predict a category for each product based on the product name, using the provided list of categories.

    Format:
    [
    {{
        "username": "{session.get('username')}",
        "item_name": "example product",
        "category": "predicted category",
        "note": "",
        "price": 1234
    }},
    ...
    ]

    Available categories: {category}
    Receipt text: {ocr_text}
    """
   
    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # ```json ... ``` を取り除く
    cleaned_text = re.sub(r"^```json|```$", "", raw_text, flags=re.MULTILINE).strip()

    # JSON配列だけ抜き出す
    match = re.search(r'\[.*\]', cleaned_text, re.DOTALL)
    if match:
        json_part = match.group(0)
        return json.loads(json_part)
    else:
        raise ValueError("Geminiから有効なJSON配列が取得できませんでした")


# 入力データを確定
@receipts_bp.route('/submit', methods=['POST'])
def handle_submit():
    data = request.get_json()
    records = data.get('records', [])
    print("受け取ったデータ:", records)

    # データをDBに保存する
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for item in records:
        c.execute('INSERT INTO items (username, date, item_name, category, note, price) VALUES (?, ?, ?, ?, ?, ?)', 
                  (session.get('username'), item[0], item[1], item[2], item[3], int(item[4])))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})
