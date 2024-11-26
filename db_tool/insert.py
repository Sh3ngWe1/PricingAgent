import json
from pymongo import MongoClient
import certifi
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.getLogger('pymongo').setLevel(logging.ERROR)
logging.getLogger('pymongo.connection').setLevel(logging.ERROR)
logging.getLogger('pymongo.server').setLevel(logging.ERROR)
logging.getLogger('pymongo.topology').setLevel(logging.ERROR)
logging.getLogger('pymongo.monitoring').setLevel(logging.ERROR)

uri = os.getenv("MONGO_URI")

# # 連接到 MongoDB
# client = MongoClient(
#     uri,
#     tls=True,
#     tlsCAFile=certifi.where()
# )
# db = client["test"]
# collection = db["market_price"]

# # 讀取 JSON 文件
# with open("../files/cost_price.json", "r", encoding="utf-8") as file:
#     data = json.load(file)

# test_data = [
#     {
#         "product_name": "Python 入門指南",
#         "cost": 150,
#         "planned_price": 399,
#     },
#     {
#         "product_name": "資料分析實戰",
#         "cost": 180,
#         "planned_price": 480,
#     },
#     {
#         "product_name": "AI 應用開發",
#         "cost": 200,
#         "planned_price": 550,
#     }
# ]

# market_data = [
#     {
#         "product_name": "Python 入門指南",
#         "data": [
#             {
#                 "title": "Python 入門指南 - 從零開始學程式設計",
#                 "price": 450,
#                 "link": "/r/?i=tw_mall_shopeemall&id=211208801.123456",
#                 "store": {
#                     "name": "博客來",
#                     "seller": ""
#                 },
#                 "created_at": "2024-11-23 17:49:56"
#             },
#             {
#                 "title": "Python 入門指南",
#                 "price": 500,
#                 "link": "/r/?i=tw_pec_books&id=0010822522",
#                 "store": {
#                     "name": "誠品線上",
#                     "seller": "誠品書店"
#                 },
#                 "created_at": "2024-11-23 17:49:56"
#             },
#             {
#                 "title": "Python 入門指南 程式設計教學",
#                 "price": 550,
#                 "link": "/r/?i=tw_mall_shopeemall&id=211208801.789012",
#                 "store": {
#                     "name": "TAAZE讀冊生活",
#                     "seller": ""
#                 },
#                 "created_at": "2024-11-23 17:49:56"
#             }
#         ]
#     },
#     {
#         "product_name": "資料分析實戰",
#         "data": [
#             {
#                 "title": "資料分析實戰：從入門到進階",
#                 "price": 520,
#                 "link": "/r/?i=tw_pec_books&id=001082253",
#                 "store": {
#                     "name": "博客來",
#                     "seller": ""
#                 },
#                 "created_at": "2024-11-23 17:49:56"
#             },
#             {
#                 "title": "資料分析實戰",
#                 "price": 570,
#                 "link": "/r/?i=tw_mall_shopeemall&id=211208801.345678",
#                 "store": {
#                     "name": "金石堂網路書店",
#                     "seller": ""
#                 },
#                 "created_at": "2024-11-23 17:49:56"
#             },
#             {
#                 "title": "資料分析實戰 - 商業應用與實例",
#                 "price": 620,
#                 "link": "/r/?i=tw_pec_momoshop&id=8572695",
#                 "store": {
#                     "name": "momo購物網",
#                     "seller": ""
#                 },
#                 "created_at": "2024-11-23 17:49:56"
#             }
#         ]
#     },
#     {
#         "product_name": "AI 應用開發",
#         "data": [
#             {
#                 "title": "AI 應用開發：理論與實務",
#                 "price": 580,
#                 "link": "/r/?i=tw_pec_books&id=001082254",
#                 "store": {
#                     "name": "博客來",
#                     "seller": ""
#                 },
#                 "created_at": "2024-11-23 17:49:56"
#             },
#             {
#                 "title": "AI 應用開發 從零開始學",
#                 "price": 630,
#                 "link": "/r/?i=tw_mall_shopeemall&id=211208801.901234",
#                 "store": {
#                     "name": "PChome 24h購物",
#                     "seller": ""
#                 },
#                 "created_at": "2024-11-23 17:49:56"
#             },
#             {
#                 "title": "AI 應用開發實戰指南",
#                 "price": 680,
#                 "link": "/r/?i=tw_pec_ybuy&id=8394987",
#                 "store": {
#                     "name": "Yahoo購物中心",
#                     "seller": ""
#                 },
#                 "created_at": "2024-11-23 17:49:56"
#             }
#         ]
#     }
# ]

# # 確保 data 是一個列表
# if not isinstance(market_data, list):
#     market_data = [market_data]

# # 將 JSON 文件存入 MongoDB
# result = collection.insert_many(market_data)

# print(f"資料已成功存入 MongoDB table: [cost_price]!")
# print(f"插入的文檔數量: {len(result.inserted_ids)}")
# # print(f"插入的文檔 ID: {result.inserted_ids}")

def insert_data(file_path):
    try:
        # 讀取 JSON 檔案
        with open(file_path, 'r', encoding='utf-8') as f:
            # 直接使用 pandas 的 JSON 字串
            data = json.loads(f.read())
        
        # 確保 data 是列表
        if not isinstance(data, list):
            raise ValueError("JSON 資料必須是列表格式")
            
        # 連接到 MongoDB
        client = MongoClient(uri, tls=True, tlsCAFile=certifi.where())
        # db = client["MarketingAgent"]
        # collection = db["cost_price"]
        db = client["MarketingAgent"]
        collection = db["cost_price_table"]
        
        # 批量插入所有資料
        result = collection.insert_many(data)
        
        print(f"成功插入 {len(result.inserted_ids)} 筆資料")
        return len(result.inserted_ids)  # 返回插入的文檔數量
        
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        return None
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    file_path = "../upload-files/20241124-153729.json"
    insert_data(file_path)
