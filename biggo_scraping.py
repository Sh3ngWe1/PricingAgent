import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import pandas as pd
import random
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi
from urllib.parse import quote
import logging
load_dotenv()

uri = os.getenv("MONGO_URI")

class BigGoScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.base_url = "https://biggo.com.tw"
        
        # 初始化 MongoDB 連接
        self.client = MongoClient(
            uri,
            tls=True,
            tlsCAFile=certifi.where()
        )
        self.db = self.client["MarketingAgent"]
        self.collection = self.db["Biggo"]

    def get_page(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"請求錯誤: {e}")
            return None

    def parse_product_list(self, html):
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # 使用 BeautifulSoup 找出所有商品項目
        product_items = soup.find_all('div', class_='ProductItemListPC_product-item-list-PC__zP1Sg')
        
        if not product_items:
            print('未找到任何商品項目')
            return []
        
        for item in product_items:
            try:
                # 取得商品標題
                title_div = item.find('div', class_='ProductItemListPC_product-title__XZPbn')
                if not title_div or not title_div.find('a'):
                    continue
                title = title_div.find('a').get('title', '').strip()
                
                # 取得商品價格
                price_div = item.find('div', class_='ProductItemListPC_product-price__ETFme')
                if not price_div:
                    continue
                price_text = price_div.text.strip()
                try:
                    price = int(price_text.replace('$', '').replace(',', ''))
                except ValueError:
                    print(f'無法解析價格: {price_text}')
                    continue
                
                # 取得商品連結
                link = title_div.find('a').get('href', '')
                if not link:
                    continue
                    
                # 取得商品圖片
                # img = item.find('img', class_='ProductImage_product-image-img__tigzB')
                # img_url = img.get('src', '') if img else ''
                # if not img_url:
                #     continue
                
                # 取得商店相關資訊
                store_link = item.find('a', class_='StoreName_store__BpLbL')
                store_name = store_link.find('span').text.strip() if store_link and store_link.find('span') else ''
                
                # 取得商店圖示URL
                # store_icon = store_link.find('img', class_='StoreIcon_store-icon-img__cJlwf') if store_link else None
                # store_icon_url = store_icon.get('src', '') if store_icon else ''
                
                # 取得賣家名稱
                seller_div = item.find('div', class_='StoreName_seller__k9nWN')
                seller = seller_div.text.strip() if seller_div else ''
                
                # 將商店相關資訊整合成一個字典
                store_info = {
                    'name': store_name,
                    # 'icon': store_icon_url,
                    'seller': seller
                }
                
                # 資料驗證
                if not all([title, price, link]):
                    print('商品資料不完整')
                    continue
                    
                # 判斷書籍類型
                book_type = "新書"  # 預設為新書
                title_lower = title.lower()
                if any(keyword in title_lower for keyword in ["二手", "二手書", "二手書籍", "回頭書"]):
                    book_type = "二手書"
                elif any(keyword in title_lower for keyword in ["電子", "電子書", "電子書籍"]):
                    book_type = "電子書"
                
                product = {
                    'title': title,
                    'price': price,
                    'link': link,
                    # 'image': img_url,
                    'store': store_info,  # 改為使用整合後的商店資訊
                    'book_type': book_type,  # 新增書籍類型欄位
                    'created_at': datetime.now()
                }
                
                products.append(product)
                
            except Exception as e:
                print(f'解析商品時發生錯誤: {str(e)}')
                continue
        
        print(f'成功解析 {len(products)} 個商品')
        return products

    # def save_to_csv(self, products, filename=None):
    #     if not filename:
    #         filename = f"biggo_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
    #     df = pd.DataFrame(products)
    #     df.to_csv(filename, index=False, encoding='utf-8-sig')
    #     print(f"資料已保存至 {filename}")

    def save_to_json(self, products, product_name, filename=None):
        # 確保資料夾存在
        output_dir = "./crawl data"
        os.makedirs(output_dir, exist_ok=True)
        
        # 設定檔案名稱和完整路徑
        if not filename:
            filename = f"{product_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        # 建立新的資料結構
        output_data = {
            "product_name": product_name,
            "data": []
        }
        
        # 將 datetime 物件轉換為字串並加入資料
        for product in products:
            product['created_at'] = product['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            output_data["data"].append(product)
            
        # 儲存到 JSON 檔案
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        print(f"資料已保存至 {filepath}")

        try:
            # 確保 data 是列表形式
            mongo_data = [output_data]

            # 插入資料到 MongoDB
            result = self.collection.insert_many(mongo_data)
            print(f"資料已成功存入 MongoDB table: [Biggo]!")
        
        except Exception as e:
            print(f"MongoDB 存儲失敗: {str(e)}")

    def scrape(self, url, max_pages=2):
        all_products = []
        page = 1
        
        while page <= max_pages:
            page_url = f"{url}?p={page}" if page > 1 else url
            print(f"正在爬取第 {page} 頁...")
            
            html = self.get_page(page_url)
            if not html:
                print(f"無法獲取第 {page} 頁的資料")
                break

            products = self.parse_product_list(html)
            if not products:
                print(f"該頁面沒有商品，停止爬取")
                break
                
            all_products.extend(products)
            
            # 避免請求過於頻繁
            time.sleep(random.uniform(1, 3))
            page += 1

        print(f"完成爬取，共爬取了 {page-1} 頁")
        return all_products

    def __del__(self):
        if hasattr(self, 'client'):
            self.client.close()

def biggo_scrape(product_names):
    try:
        for product_name in product_names:
            # 使用 quote 對中文進行 URL 編碼
            encoded_name = quote(product_name)
            url = f"https://biggo.com.tw/s/{encoded_name}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                # 處理回應...
                logging.info(f"成功抓取 {product_name} 的資料")
            else:
                logging.error(f"抓取 {product_name} 失敗: {response.status_code}")
                
    except Exception as e:
        logging.error(f"爬蟲過程發生錯誤: {str(e)}")
        raise

if __name__ == "__main__":
    # product_name = "原子習慣：細微改變帶來巨大成就的實證法則"
    # product_name = "情緒掌控，決定你的人生格局：別讓1%的情緒失控，毀了你99%的努力"

    # product_name = input("請輸入商品名稱: ")
    product_names = ["在大雪封閉的山莊裡【電影書腰限量珍藏版】", "消失物誌（二版）", "要吃？不吃？—Homework 家庭號特輯", "假裝是魚", "DP中文A文學課程試卷1文學分析優秀範文點評（第二版）（繁體版）"]

    biggo_scrape(product_names)