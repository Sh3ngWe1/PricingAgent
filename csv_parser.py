import pandas as pd
import json
from datetime import datetime
from db_tool.insert import insert_data

def read_excel_file(file_path):
    try:
        # 使用 pandas 讀取 Excel 檔案
        df = pd.read_excel(file_path)
        
        # 移除「項次」欄位
        if '項次' in df.columns:
            df = df.drop('項次', axis=1)
        
        # 重新命名欄位
        df = df.rename(columns={
            '店內碼': 'store_code',
            '商品名稱': 'product_name',
            '售價': 'price',
            '成本': 'cost'
        })
        
        # 將 DataFrame 轉換成 JSON 格式
        json_data = df.to_json(orient='records', force_ascii=False, indent=2)
        
        # 將 JSON 存成檔案
        with open('files/cost_price.json', 'w', encoding='utf-8') as f:
            f.write(json_data)
                
        return json_data
            
    except FileNotFoundError:
        print(f"找不到檔案: {file_path}")
        return None
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        return None

def parse_csv(file_path):
    try:
        # 使用 pandas 讀取 Excel 檔案
        df = pd.read_excel(file_path)
        print(f"讀取到 {len(df)} 筆資料")  # 除錯訊息
        
        # 取得所有商品名稱列表
        product_names = df['商品名稱'].tolist()
        
        # 移除「項次」欄位
        if '項次' in df.columns:
            df = df.drop('項次', axis=1)
        
        # 重新命名欄位
        df = df.rename(columns={
            '店內碼': 'store_code',
            '商品名稱': 'product_name',
            '售價': 'price',
            '成本': 'cost'
        })
        
        # 生成輸出檔案名稱
        current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file_path = f'upload-files/{current_time}.json'
        
        # 將 DataFrame 轉換成 JSON 格式並儲存
        json_data = df.to_json(orient='records', force_ascii=False, indent=2)
        
        # 檢查轉換後的 JSON 資料
        parsed_data = json.loads(json_data)
        print(f"轉換為 JSON 後有 {len(parsed_data)} 筆資料")  # 除錯訊息
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
            
        print(f"已寫入檔案：{output_file_path}")  # 除錯訊息
        
        # result = insert_data(output_file_path)
        # print(f"插入結果：{result}")  # 除錯訊息
            
        return output_file_path, product_names  # 回傳檔案路徑和商品名稱列表
            
    except Exception as e:
        raise Exception(f"處理 Excel 檔案時發生錯誤: {str(e)}")

# 使用範例
if __name__ == "__main__":
    file_path = "upload-files/1000_.xls"
    data = parse_csv(file_path)
    # print(data)