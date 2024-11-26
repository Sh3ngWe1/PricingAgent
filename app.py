import logging
from flask import Flask, request, jsonify, render_template
import os
from flask_cors import CORS
from market import  update_planned_price, get_cost_price, get_market_price, ai_suggest_price, analyze_price_competitiveness
from csv_parser import parse_csv
from werkzeug.utils import secure_filename
from biggo_scraping import biggo_scrape

# 關閉所有 MongoDB 相關的日誌
logging.getLogger('pymongo').setLevel(logging.ERROR)
logging.getLogger('pymongo.connection').setLevel(logging.ERROR)
logging.getLogger('pymongo.server').setLevel(logging.ERROR)
logging.getLogger('pymongo.topology').setLevel(logging.ERROR)
logging.getLogger('pymongo.monitoring').setLevel(logging.ERROR)

app = Flask(__name__, template_folder=os.path.abspath('templates'))
CORS(app)

# 設定上傳檔案的資料夾
UPLOAD_FOLDER = 'upload-files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 檢查並建立 ./docs 資料夾
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)

# 設定允許的檔案格式
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

# 設置日誌
logging.basicConfig(level=logging.DEBUG)

# 確保上傳資料夾存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, mode=0o755, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/test', methods=['POST'])
def test():
    try:
        return jsonify({"data": "Hello, World!"})
    except Exception as e:
        app.logger.error(f"handle_chat 錯誤: {str(e)}")
        return jsonify({"error": "內部伺服器錯誤"}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update-planned-price', methods=['POST'])
def update_price():
    try:
        data = request.get_json()
        print("================================")
        print(data)
        print("================================")
        product_name = data.get('product_name')
        planned_price = data.get('planned_price')
        
        # 這裡加入更新資料庫的程式碼
        update_planned_price(product_name, planned_price)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/book-info', methods=['POST'])
def get_book_info():
    try:
        data = request.get_json()
        book_name = data.get('product_name')
        shipping_cost = data.get('shipping_cost', 0)
        platform_cost = data.get('platform_cost', 0)
        
        if not book_name:
            return jsonify({'error': '請提供書名'}), 400
            
        # 只取得指定書籍的資訊
        cost_info = get_cost_price(book_name)  # 這是一個字典
        market_price = get_market_price(book_name)
        
        # 從字典中取得實際的成本值
        cost = cost_info.get('cost')
        planned_price = cost_info.get('price')
        suggested_price = ai_suggest_price(book_name, shipping_cost, platform_cost)
        
        # 只返回這一本書的資訊
        return jsonify({
            'cost': cost,
            'market_price': market_price,
            'suggested_price': suggested_price,
            'planned_price': planned_price
        })
        
    except Exception as e:
        app.logger.error(f"取得書籍資訊時發生錯誤: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/upload-files', methods=['POST'])
def upload_books():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '沒有上傳檔案'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '沒有選擇檔案'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': '只支援 .xls 或 .xlsx 檔案'}), 400

        # 儲存檔案
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # 使用 parse_csv 處理檔案
            result = parse_csv(file_path)
            output_file_path = result[0]
            product_names = result[1]

            # for product_name in product_names:
            #     biggo_scrape(product_name)

            # 分析價格競爭力
            warning_list = analyze_price_competitiveness(product_names)
            
            return jsonify({
                'success': True,
                'message': '檔案上傳成功',
                'output_file_path': output_file_path,
                'warning_list': warning_list  # 只回傳需要警告的書籍清單
            })
        except Exception as e:
            return jsonify({'error': f'檔案處理失敗: {str(e)}'}), 400
            
    except Exception as e:
        app.logger.error(f"上傳檔案時發生錯誤: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=4040, debug=True)
