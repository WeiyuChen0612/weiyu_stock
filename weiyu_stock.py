import requests
import json
import time
import pandas as pd
from datetime import datetime
import yfinance as yf


NAME_MAP = {
    "2330.TW": "台積電", "2317.TW": "鴻海", "2382.TW": "廣達", "3231.TW": "緯創", "2376.TW": "技嘉", "6669.TW": "緯穎", "2303.TW": "聯電", "3711.TW": "日月光投控", "2449.TW": "京元電子",
    "3374.TWO": "精材", "3131.TWO": "弘塑", "6187.TWO": "萬潤", "3017.TW": "奇鋐", "3324.TWO": "雙鴻",
    "2454.TW": "聯發科", "3037.TW": "欣興", "2313.TW": "華通",
    "2308.TW": "台達電", "1513.TW": "中興電", 
    "2408.TW": "南亞科", "2344.TW": "華邦電", "3006.TW": "晶豪科", "8299.TWO": "群聯",
    "2327.TW": "國巨", "2492.TW": "華新科", "3026.TW": "禾伸堂", "3624.TWO": "光頡",
    "6488.TWO": "環球晶", "3532.TW": "台勝科",
    "3019.TW": "亞光", "6223.TWO": "旺矽", 
    "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2886.TW": "兆豐金",
    "2610.TW": "華航", "2618.TW": "長榮航", "2609.TW": "陽明", "2603.TW": "長榮","2646.TW": "星宇", 
    "2634.TW": "漢翔", "4572.TW": "駐龍", "8033.TW": "雷虎", "3003.TW": "健和興"
}

SECTOR_DATA = {
    "AI與半導體": ["2330.TW", "2317.TW", "2382.TW", "3231.TW", "2376.TW", "6669.TW", "2303.TW", "3711.TW", "2449.TW"],
    "IC設計與載板": ["2454.TW", "3037.TW", "2313.TW"],
    "先進封裝與散熱": ["3374.TWO", "3131.TWO", "6187.TWO", "3017.TW", "3324.TWO"],
    "電力與能源": ["2308.TW", "1513.TW"],
    "記憶體與矽晶圓": ["2408.TW", "2344.TW", "3006.TW", "8299.TWO", "6488.TWO", "3532.TW"],
    "被動元件": ["2327.TW", "2492.TW", "3026.TW", "3624.TWO"],
    "光學與檢測": ["3019.TW", "6223.TWO"],
    "金融機構": ["2881.TW", "2882.TW", "2891.TW", "2886.TW"],
    "航運航空": ["2610.TW", "2618.TW", "2646.TW", "2609.TW", "2603.TW"],
    "國防軍工": ["2634.TW", "4572.TW", "8033.TW", "3003.TW"]
}

def get_real_institutional_data():
    """抓取證交所官方盤後法人買賣超，並自動偵測欄位"""
    date_str = datetime.now().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={date_str}&selectType=ALL&response=json"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
        if 'data' not in res or not res['data']:
            print("⚠️ 證交所目前尚無今日法人資料。")
            return {}
        
        df = pd.DataFrame(res['data'], columns=res['fields'])
        
        # 自動查找包含關鍵字的欄位名稱
        def find_col(keywords):
            for col in df.columns:
                if all(kw in col for kw in keywords): return col
            return None

        # 證交所欄位常見名稱：'外資及陸資買賣超股數', '投信買賣超股數'
        col_foreign = find_col(['外資', '陸資'])
        col_sitc = find_col(['投信'])
        
        if not col_foreign or not col_sitc:
            print(f"❌ 找不到欄位，目前清單: {list(df.columns)}")
            return {}

        df[col_foreign] = df[col_foreign].astype(str).str.replace(',', '').astype(int)
        df[col_sitc] = df[col_sitc].astype(str).str.replace(',', '').astype(int)
        
        fund_map = {}
        for _, row in df.iterrows():
            code = f"{row['證券代號']}.TW"
            fund_map[code] = row[col_foreign] + row[col_sitc]
        return fund_map
    except Exception as e:
        print(f"❌ 抓取證交所失敗: {e}")
        return {}

def get_data():
    now = datetime.now()
    # 修正時間判斷：下午 2:30 (870分鐘) 後觸發
    current_minutes = now.hour * 60 + now.minute
    is_after_hours = current_minutes >= 870
    
    fund_data = get_real_institutional_data() if is_after_hours else {}
    
    final_output = []
    print(f"--- 模式: {'盤後精準數據' if is_after_hours else '盤中即時模擬'} ---")
    
    for sector_name, stock_list in SECTOR_DATA.items():
        total_vol = 0
        stock_details = []
        
        for ticker in stock_list:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    vol = int(hist['Volume'].iloc[-1])
                    change_pct = round(((current_price - prev_price) / prev_price) * 100, 2)
                    total_vol += vol
                    
                    buy_power = fund_data.get(ticker, 0)
                    
                    stock_details.append({
                        "name": ticker, 
                        "display_name": NAME_MAP.get(ticker, ticker),
                        "buy_vol": int(vol * 0.55), 
                        "sell_vol": int(vol * 0.45),
                        "price": round(current_price, 2),
                        "change": change_pct,
                        "buy_power": buy_power,
                        "warning": "🔥" if buy_power > 100000 else ""
                    })
            except Exception as e:
                print(f"  ! {ticker} 抓取失敗: {e}")
            time.sleep(0.6)
            
        final_output.append({"name": sector_name, "x": round(total_vol/100000, 2), "details": stock_details})

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(f"var stockData = {json.dumps(final_output, ensure_ascii=False)};")
    print("✅ data.js 更新完畢！")

if __name__ == "__main__":
    get_data()
