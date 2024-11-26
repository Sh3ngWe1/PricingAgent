"""
要有的幾個def:
1. 取得書籍的市場售價
2. 取得書籍的成本及預訂售價
3. 根據書籍的市場售價及成本，推薦價格並計算毛利率
4. 提供行銷策略
5. 「跟價」系統 -> 前端網頁會有像這樣的表格：
    （他會先根據書名找出成本及預定售價，然後和其他通路之售價做比較，找出沒有市場競爭力的書籍，然後AI會根據書籍類型及市場趨勢，提供行銷策略，然後我可以在前端直接輸入修改建議售價，然後AI會根據市場售價及成本，推薦價格並計算毛利率）
    - 書名
    - 成本
    - 市場售價
    - 預定售價
    - 建議售價（根據市場售價及成本，推薦的價格）(我可以在前端直接輸入修改)
    - 毛利率（real time 根據建議售價和成本去計算）
    - 行銷策略（根據書籍類型及市場趨勢，提供行銷策略）
    - 其他行銷資訊（自行輸入，讓AI可以根據這個想法加上上面的價格資訊來做行銷策略推薦）
    - 跟價按鈕（按下後AI會根據“建議售價”這格的價格，去跟其他通路比價，並輸出比較結果及建議以及最重要的若使用此價格之毛利率）如果用戶確認，則更新後端資料庫之售價
6. 我要可以輸入一堆書名，然後AI一次處理完畢，輸出表格
"""

import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pymongo import MongoClient
import certifi
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.environ["MONGO_URI"]

gpt4oModel = ChatOpenAI(model="gpt-4o-mini",temperature=0.1)

def get_market_price(book_name:str):
    client = MongoClient(
        uri,
        tls=True,
        tlsCAFile=certifi.where()
    )
    db = client["MarketingAgent"]
    collection = db["Biggo"]
    # query = {"product_name": {"$regex": book_name, "$options": "i"}}
    query = {"product_name": book_name, "data.book_type": "新書"}
    projection = {"data.price": 1, "data.store.name": 1 , "_id": 0}
    result = collection.find_one(query, projection)
    
    # 從結果中提取價格列表
    if result and 'data' in result:
        return {item['store']['name']: item['price'] for item in result['data']}
    return {}

def get_cost_price(book_name:str):
    client = MongoClient(
        uri,
        tls=True,
        tlsCAFile=certifi.where()
    )
    db = client["test"]
    collection = db["book"]
    # query = {"product_name": {"$regex": book_name, "$options": "i"}}
    query = {"product_name": book_name}
    projection = {"cost": 1, "price": 1, "_id": 0}
    result = collection.find_one(query, projection)
    return result

def update_planned_price(book_name:str, planned_price:int):
    try:
        client = MongoClient(
            uri,
            tls=True,
            tlsCAFile=certifi.where()
        )
        db = client["test"]
        collection = db["book"]
        result = collection.update_one(
            {"product_name": book_name}, 
            {
                "$set": {
                    "price": planned_price
                }
            }
        )
        
        # 檢查是否有成功更
        if result.modified_count == 0:
            print(f"Warning: No document was updated for book: {book_name}")
            return False  # 如果沒有更新任何文檔
        return True      # 如果成功更新
        
    except Exception as e:
        print(f"Error updating price: {str(e)}")
        raise e
    finally:
        client.close()

def ai_suggest_price(book_name:str, shipping_cost:float=0, platform_cost:float=0):
    cost = get_cost_price(book_name)["cost"]
    price = get_cost_price(book_name)["price"]
    market_price = get_market_price(book_name)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                你是一個價格分析專家，請根據書籍成本（包含運費）、平台抽成、市場售價、預定售價，推薦一個合理的售價，請確保只回傳數字部分，不要包含其他文字
                """
            ),
            (
                "user",
                """
                書名：{book_name}
                基礎成本：{cost}
                運費：{shipping_cost}
                平台抽成：{platform_cost}%
                市場售價：{market_price_formatted}
                預定售價：{price}
                """
            )
        ]
    )

    market_price_formatted = "\n".join([f"- 通路{i+1}：${price}" for i, price in enumerate(market_price)])

    suggest_price_result = prompt | gpt4oModel
    result = suggest_price_result.invoke(
        {
            "book_name": book_name,
            "cost": cost,
            "shipping_cost": shipping_cost,
            "platform_cost": platform_cost,
            "market_price_formatted": market_price_formatted,
            "price": price,
        }
    )

    try:
        return int(result.content.strip())
    except ValueError:
        print(f"無法將價格轉換為整數：{result.content}")
        return None

def analyze_price_competitiveness(product_names: list) -> list:
    warning_list = []
    total_books = len(product_names)
    
    print(f"\n開始分析 {total_books} 本書的價格競爭力...")
    
    # 準備書籍資訊
    books_info = []
    for index, book_name in enumerate(product_names, 1):
        print(f"\n處理第 {index}/{total_books} 本: {book_name}")
        
        cost_info = get_cost_price(book_name)
        print(f"- 取得成本資訊: {cost_info}")
        
        market_prices = get_market_price(book_name)
        print(f"- 取得市場價格: {market_prices}")
        
        if cost_info and market_prices:
            book_info = (
                f"書名：{book_name}\n"
                f"成本：{cost_info['cost']}\n"
                f"預定售價：{cost_info['price']}\n"
                f"市場售價：{market_prices}\n"
                "---"
            )
            books_info.append(book_info)
            print("- 資訊整理完成")
        else:
            print("- 缺少必要資訊，跳過此書")
    
    books_info_str = "\n".join(books_info)
    
    print("\n開始進行 AI 分析...")
    
    # 使用 JsonOutputParser 確保輸出格式正確
    output_parser = JsonOutputParser()
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            你是一個價格分析專家。請分析每本書的價格競爭力，找出需要警告的書籍。
            判斷標準：
            1. 預定售價明顯高於市場均價（超過15%）
            2. 預定售價低於成本或毛利率過低（低於20%）
            3. 預定售價與市場價格差異過大
            
            請只回傳需要警告的書名列表，格式為 JSON array。
            """
        ),
        (
            "user",
            """
            書籍資訊：
            {books_info}
            """
        )
    ])
    
    chain = prompt | gpt4oModel | output_parser
    
    try:
        result = chain.invoke({"books_info": books_info_str})
        warning_list = result if isinstance(result, list) else []
        print(f"\nAI 分析完成，發現 {len(warning_list)} 本需要注意的書籍")
        print(f"需要注意的書籍：{warning_list}")
    except Exception as e:
        print(f"\n分析過程發生錯誤：{str(e)}")
        warning_list = []
    
    return warning_list

if __name__ == "__main__":
    print("Hello")
    # print(get_marketing_strategy("Python 入門指南", 150, [450, 400, 350], 170))
    # print("--------------------------------")
    # print(get_marketing_strategy("資料分析實戰", 180, [520, 480, 450], 480))
    # print("--------------------------------")
    # print(get_marketing_strategy("AI 應用開發", 200, [580, 550, 520], 550)) 
    # print(get_market_price("Python 入門指南"))
    # print("price:", get_cost_price("Python 入門指南")["price"])
    # print("cost:", get_cost_price("Python 入門指南")["cost"])
    # update_planned_price("Python 入門指南", 399)
    # print(ai_suggest_price("Python 入門指南"))
