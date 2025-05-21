from flask import Flask, Blueprint, render_template, request, jsonify
import base64
import os
from io import BytesIO
from PIL import Image
import pytesseract
from dotenv import load_dotenv
import cv2
import numpy as np

receipts_bp = Blueprint('receipts', __name__, url_prefix='/receipts')

load_dotenv()
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH')

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# レシート読み取り
@receipts_bp.route('/upload', methods=['POST'])
def upload_receipt():
    data = request.get_json()

    if not data or 'image' not in data:
        return jsonify({'error': '画像データがありません'}), 400

    image_data = data['image']

    try:
        # base64デコード
        header, encoded = image_data.split(",", 1)
        image_binary = base64.b64decode(encoded)

        # 画像として開く
        image = Image.open(BytesIO(image_binary))
        
        cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        image = Image.fromarray(thresh)

        image.show()

        # OCR実行
        text = pytesseract.image_to_string(image, lang='jpn')
        print("OCR結果:", repr(text))

        # テキスト保存
        with open('output.txt', 'w', encoding='utf-8') as f:
            f.write(text)

        print("抽出したテキストをoutput.txtに保存しました。")

        return jsonify({'status': 'ok', 'text': text})

    except Exception as e:
        print("エラー:", e)
        return jsonify({'error': str(e)}), 500


# 入力データを確定
@receipts_bp.route('/submit', methods=['POST'])
def handle_submit():
    data = request.get_json()
    records = data.get('records', [])
    print("受け取ったデータ:", records)

    # DB保存などの処理

    return jsonify({"status": "ok"})
