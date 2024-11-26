import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from pymongo import MongoClient
import certifi
import pymongo
from openai import OpenAI
import logging
import sys


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

logging.getLogger("pymongo").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv()
openai_client = OpenAI()
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "MarketingAgent-0.1"
os.environ["MONGO_URI"] = os.getenv("MONGO_URI")

uri = os.environ["MONGO_URI"]

# 連接 MongoDB
client = MongoClient(
    uri,
    tls=True,
    tlsCAFile=certifi.where()
)
db = client["MarketingAgent"]


# Load the LLM model
gpt4oModel = ChatOpenAI(model="gpt-4o-mini")


# Tools
@tool
def check_weather(city: str):
    """
    取得指定城市的氣象資訊。
    """
    return f"{city}溫度約19~23度。降雨機率0%。"

@tool
def get_biggo_book_price(book_name: str):
    """
    取得指定書不同販售通路的售價。
    """
    # print("book_name: ", book_name)
    collection = db["Biggo"]
    query = {"product_name": {"$regex": book_name, "$options": "i"}}
    projection = { "data.store.name": 1, "data.store.seller": 1, "data.price": 1, "data.book_type": 1, "_id": 0 }
    result = collection.find_one(query, projection)
    # print(result)   
    return result

@tool
def get_cost_price(book_name: str):
    """
    取得本書店中指定書籍的成本及預訂售價。
    """
    # print("book_name: ", book_name)
    collection = db["cost_price"]
    query = {"product_name": {"$regex": book_name, "$options": "i"}}
    projection = { "cost": 1, "price": 1, "_id": 0 }
    result = collection.find_one(query, projection)
    # print(result)   
    return result

tools = [
    check_weather,
    get_biggo_book_price,
    get_cost_price
]

system_prompt = """請回答用戶問題，並且提供資訊的分析。"""

# Create graph
graph = create_react_agent(gpt4oModel, tools, state_modifier=system_prompt)


# 使用範例
if __name__ == "__main__":
    # print("Hello, World!")
    inputs = {
            "messages": [
                (
                    "user",
                    "請你找出「假裝是魚」這本書（新書）在市場上的售價情況為何，並且和本書店的成本及預訂售價做比較。",
                ),
                ("user", "1. 請給我一個合理，且能有市場競爭力的售價。請你參考這本書在其他通路中較常見的售價，請不要考慮過高或過低的價格。"),
                ("user", "2. 請提供不同售價策略的毛利率。不需要提供計算過程，只需要提供結果。"),
                ("user", "3. 你是一位行銷專家，請你提供3個行銷計畫，包含行銷策略、預算、預期效果、預期效益。"),
                ("user", "4. 另外我希望毛利率都控制在15~20%之間。")
            ]
        }

    result = None
    for s in graph.stream(inputs, stream_mode="values"):
        message = s["messages"][-1]
        if isinstance(message, tuple):
            result = message[1]
        else:
            result = message.content
    
    print(result)

