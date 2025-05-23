from flask import Flask, Blueprint, render_template, request, jsonify
import base64
import os
from io import BytesIO
from PIL import Image
import pytesseract
from dotenv import load_dotenv  # 環境変数の読み込み
import google.generativeai as genai

receipts_bp = Blueprint('receipts', __name__, url_prefix='/receipts')

load_dotenv()
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH')

# Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# リストを追加

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
        image_binary = base64.b64decode(encoded.encode('utf-8'))
        image = Image.open(BytesIO(image_binary))
        image.show()

        # 画像解析
        ocr_text = extract_text_from_image(image)   
        print("OCR結果：\n", ocr_text)

        list = parse_receipt_with_gemini(ocr_text)
        print("Geminiの出力：\n", list)

        return jsonify(list)

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



# 画像処理
def extract_text_from_image(image):
    #gray = cv2.cvtColor(image, cv2.COLORBGR2GRAY)
    #gray = cv2.medianBlur(gray, 3)
    #thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY   cv2.THRESH_OTSU)

    return pytesseract.image_to_string(image, lang="jpn")

# Geminiに解析依頼
def parse_receipt_with_gemini(ocr_text):
    prompt = f"""
次のレシートの内容から、商品名と金額を抽出して、以下の形式のJSONリストにしてください。

[{{"商品名": "xxx", "金額": xxx}}, ...]

レシート内容:
{ocr_text}
"""
    response = model.generate_content(prompt)
    return response.text