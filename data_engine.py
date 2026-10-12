import cloudscraper
import requests
import yfinance as yf
import random
from bs4 import BeautifulSoup
from datetime import datetime


# 1. Live USD/BDT Exchange Rate API (Updated with yfinance for History & Delta)
def get_live_usd_rate():
    try:
        # BDT=X is the ticker for USD to BDT on Yahoo Finance
        ticker = yf.Ticker("BDT=X")
        hist = ticker.history(period="1d", interval="1m")  # 1 day history with 1 minute intervals
        
        if not hist.empty and len(hist) >= 2:
            current_rate = float(hist['Close'].iloc[-1])
            prev_rate = float(hist['Close'].iloc[-2])
            change_pct = ((current_rate - prev_rate) / prev_rate) * 100
            history_list = hist['Close'].tolist()
            
            # ডাটাগুলোকে ডিকশনারি হিসেবে পাঠানো হচ্ছে
            return {
                "price": round(current_rate, 2),
                "change": round(change_pct, 2),
                "history": history_list
            }
    except Exception as e:
        print(f"Currency Fetch Error: {e}")
        pass
    
    # Fallback Data (Dictionary format)
    return {
        "price": 118.50,
        "change": 0.0,
        "history": [117, 117.5, 118, 118.5, 118.5]
    }

# 2. Web Scraper (Bypassing Bot Protection)
def get_live_product_price(url):

    # Cloudscraper তৈরি করা যা ব্রাউজারের মতো কাজ করবে
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    try:
        response = scraper.get(url)

        # যদি সাইট ব্লক করে দেয়, তাহলে স্ট্যাটাস কোড ২০০ এর বদলে অন্য কিছু আসবে
        if response.status_code != 200:
            print(f"[Error] Website Blocked or Down! Status Code: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # StarTech এর প্রাইস ক্লাস
        price_element = soup.find(class_='product-price')
        
        if price_element:
            price_text = price_element.text
            
            # পুরো টেক্সটকে '৳' চিহ্ন দিয়ে ভাগ করে প্রথম দামটা আলাদা করা
            actual_price_text = price_text.split('৳')[0]

            # শুধু সংখ্যা বের করে আনা
            clean_price = int(''.join(filter(str.isdigit, actual_price_text)))
            return clean_price
        else:
            print("[Error] Price tag not found on this page. Product might be Out of Stock.")
            return None
            
    except Exception as e:
        print(f"[Error] Scraping Failed: {e}")
        return None
    
# 3. Global Market Indicators (Gold, Oil, S&P 500) with Daily Change (With Smart Fallback)
def get_global_indicators():
    try:
        tickers = yf.Tickers('GC=F CL=F ^GSPC')
        hist_gold = tickers.tickers['GC=F'].history(period="7d")
        hist_oil = tickers.tickers['CL=F'].history(period="7d")
        hist_sp500 = tickers.tickers['^GSPC'].history(period="7d")
        
        # ডাটা না পেলে রিয়ালিস্টিক ডামি হিস্টোরি দেখানোর ব্যবস্থা
        def process_data(hist_data, fallback_price, fallback_hist):
            if len(hist_data) >= 2:
                current_price = float(hist_data['Close'].iloc[-1])
                previous_price = float(hist_data['Close'].iloc[-2])
                change_pct = ((current_price - previous_price) / previous_price) * 100
                history_list = hist_data['Close'].tolist()
                return round(current_price, 2), round(change_pct, 2), history_list
            return fallback_price, 0.0, fallback_hist

        # Yahoo API ফেইল করলে এই ব্যাকআপ ডাটাগুলো শো করবে
        dummy_hist = [0, 1, 2, 3, 2, 4, 5] 
        gold_price, gold_change, gold_hist = process_data(hist_gold, 2350.50, dummy_hist)
        oil_price, oil_change, oil_hist = process_data(hist_oil, 82.30, dummy_hist)
        sp_price, sp_change, sp_hist = process_data(hist_sp500, 5200.10, dummy_hist)
        
        return {
            "Gold": {"price": gold_price, "change": gold_change, "history": gold_hist},
            "Oil": {"price": oil_price, "change": oil_change, "history": oil_hist},
            "SP500": {"price": sp_price, "change": sp_change, "history": sp_hist}
        }
    except Exception as e:
        print(f"Finance API Error: {e}")
        # ক্র্যাশ এড়াতে ফলব্যাক রিটার্ন
        dummy_hist = [0, 1, 2, 3, 2, 4, 5]
        return {
            "Gold": {"price": 2350.50, "change": 0.0, "history": dummy_hist},
            "Oil": {"price": 82.30, "change": 0.0, "history": dummy_hist},
            "SP500": {"price": 5200.10, "change": 0.0, "history": dummy_hist}
        }

# Testing the functions
if __name__ == "__main__":
    usd_rate, usd_change, usd_history = get_live_usd_rate()
    print(f"Live USD Rate: ৳ {usd_rate}")
    print(f"USD Change: {usd_change}%")
    print(f"Fetching Global Indicators: {get_global_indicators()}")
    # StarTech-এর একটি ভ্যালিড প্রোডাক্ট লিংক (MacBook M3)
    test_url = "https://www.startech.com.bd/apple-macbook-air-m5-15-inch"
    
    print("Scraping Data... Please wait.")
    live_price = get_live_product_price(test_url)
    
    if live_price:
        print(f"Live MacBook Price: ৳ {live_price}")
    else:
        print("Failed to get price. Check the errors above.")



def get_national_market_pulse():
    """
    Simulates the National Macro Market Data for BD Gadget/Electronics sector.
    In Phase 2, this will be replaced by actual Web Scrapers (Daraz/Facebook) and Crowdsourced Shadow Data.
    """
    # Using current hour to create dynamic fluctuations
    current_hour = datetime.now().hour
    volatility = random.uniform(-2.0, 5.0)
    
    # Base national metrics
    base_volume = 1250000000 # 1.25 Billion BDT base
    live_volume = base_volume + (current_hour * 15000000) + (volatility * 1000000)
    
    return {
        "market_volume": f"৳ {live_volume / 1000000000:.2f}B",
        "volume_change": f"{'+' if volatility > 0 else ''}{volatility:.1f}% (24h)",
        "active_wholesalers": random.randint(340, 380),
        "sentiment": "🔥 Bullish" if volatility > 0 else "🩸 Bearish",
        "avg_margin": f"{18.5 + (volatility/10):.1f}%",
        "trending_sector": "TWS & Audio" if current_hour % 2 == 0 else "Smart Wearables",
        "struggling_sector": "PC Components" if current_hour % 2 == 0 else "Wired Accessories"
    }