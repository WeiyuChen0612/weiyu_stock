import yfinance as yf
import json
import time

NAME_MAP = {
    # AI/伺服器/先進封裝
    "2330.TW": "台積電", "2317.TW": "鴻海", "2382.TW": "廣達", "3231.TW": "緯創", "2376.TW": "技嘉", "6669.TW": "緯穎", "2303.TW": "聯電", "3711.TW": "日月光投控", "2449.TW": "京元電子",
    "3374.TWO": "精材", "3131.TWO": "弘塑", "6187.TWO": "萬潤", "3017.TW": "奇鋐", "3324.TWO": "雙鴻",
    # IC設計與載板
    "2454.TW": "聯發科", "3037.TW": "欣興", "2313.TW": "華通",
    #電力與能源
    "2308.TW": "台達電", "1513.TW": "中興電", 
    # 記憶體/被動元件/矽晶圓
    "2408.TW": "南亞科", "2344.TW": "華邦電", "3006.TW": "晶豪科", "8299.TWO": "群聯",
    "2327.TW": "國巨", "2492.TW": "華新科", "3026.TW": "禾伸堂", "3624.TWO": "光頡",
    "6488.TWO": "環球晶", "3532.TW": "台勝科",
    #光學與檢測
    "3019.TW": "亞光", "6223.TWO": "旺矽", 
    # 金融股
    "2881.TW": "富邦金", "2882.TW": "國泰金", "2891.TW": "中信金", "2886.TW": "兆豐金",
    # 航空貨運
    "2610.TW": "華航", "2618.TW": "長榮航", "2609.TW": "陽明", "2603.TW": "長榮","2646.TW": "星宇", 
    # 軍工股
    "2634.TW": "漢翔", "4572.TW": "駐龍", "8033.TW": "雷虎", "3003.TW": "健和興"
}

# 整合後的完整產業分類
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
def get_data():
    final_output = []
    print(f"--- 正在更新數據 ---")
    
    for sector_name, stock_list in SECTOR_DATA.items():
        total_vol = 0
        stock_details = []
        
        for ticker in stock_list:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change_pct = round(((current_price - prev_price) / prev_price) * 100, 2)
                    vol = int(hist['Volume'].iloc[-1])
                    
                    buy_vol = int(vol * 0.55)
                    sell_vol = int(vol * 0.45)
                    # 模擬法人買超 (以總量的 5% 為基準)
                    buy_power = int(vol * 0.05)
                    # 計算集中度：若買超超過總量 10% 則標記活躍
                    is_active = (buy_power / vol) > 0.1 
                    
                    total_vol += vol
                    stock_details.append({
                        "name": ticker, 
                        "display_name": NAME_MAP.get(ticker, ticker),
                        "buy_vol": buy_vol, 
                        "sell_vol": sell_vol,
                        "price": round(current_price, 2),
                        "change": change_pct,
                        "buy_power": buy_power,
                        "warning": "🔥" if is_active else ""
                    })
            except Exception as e:
                print(f"  ! 跳過 {ticker}: {e}")
            time.sleep(0.5)
            
        final_output.append({
            "name": sector_name, 
            "x": round(total_vol/100000, 2), 
            "y": round((total_vol/100000)*0.8, 2),
            "details": stock_details
        })

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(f"var stockData = {json.dumps(final_output, ensure_ascii=False)};")
    print("✅ data.js 更新完畢！")

if __name__ == "__main__":
    get_data()