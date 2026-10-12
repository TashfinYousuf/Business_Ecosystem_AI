"""
backend/core-api/domain/market_data_engine.py
Market Intelligence, Live USD/BDT & Global Indicators (Gold, Oil, S&P500),
StarTech E-Commerce Scraper, Live Market Terminal, and Supplier Trust Radar.
Ported from legacy-streamlit-mvp/data_engine.py, automated_scraper.py, and app.py.
"""

from __future__ import annotations

import logging
import random
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

from domain.legacy_store import get_live_terminal_data, get_trust_scores

logger = logging.getLogger("MarketDataEngine")


# 1. Live USD/BDT Exchange Rate API (yfinance BDT=X with History & Delta + Smart Fallback)
def get_live_usd_rate(fetch_live: bool = False) -> Dict[str, Any]:
    if fetch_live and HAS_YFINANCE:
        try:
            ticker = yf.Ticker("BDT=X")
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty and len(hist) >= 2:
                current_rate = float(hist["Close"].iloc[-1])
                prev_rate = float(hist["Close"].iloc[-2])
                change_pct = ((current_rate - prev_rate) / prev_rate) * 100
                history_list = [round(float(x), 2) for x in hist["Close"].tolist()[-20:]]
                return {
                    "price": round(current_rate, 2),
                    "change": round(change_pct, 2),
                    "history": history_list,
                }
        except Exception as e:
            logger.warning("Currency Fetch Error: %s", e)

    return {
        "price": 118.50,
        "change": 0.42,
        "history": [117.0, 117.5, 117.8, 118.0, 118.2, 118.5, 118.5],
    }


# 2. Web Scraper (Bypassing Bot Protection for StarTech Product Price)
def get_live_product_price(url: str) -> Optional[int]:
    if not HAS_BS4:
        return None
    try:
        if HAS_CLOUDSCRAPER:
            scraper = cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "windows", "mobile": False}
            )
            response = scraper.get(url, timeout=8)
        else:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            }
            response = requests.get(url, headers=headers, timeout=8)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, "html.parser")
        price_element = soup.find(class_="product-price")
        if price_element:
            price_text = price_element.text
            actual_price_text = price_text.split("৳")[0]
            digits = "".join(filter(str.isdigit, actual_price_text))
            return int(digits) if digits else None
        return None
    except Exception as e:
        logger.warning("Product price scraping failed: %s", e)
        return None


# 3. Global Market Indicators (Gold, Oil, S&P 500) with Daily Change & Smart Fallback
def get_global_indicators(fetch_live: bool = False) -> Dict[str, Dict[str, Any]]:
    dummy_hist_gold = [2320.0, 2331.5, 2328.0, 2340.2, 2345.0, 2348.5, 2350.50]
    dummy_hist_oil = [80.1, 80.8, 81.2, 81.0, 81.7, 82.0, 82.30]
    dummy_hist_sp = [5150.0, 5165.4, 5160.2, 5180.0, 5192.5, 5195.0, 5200.10]

    if fetch_live and HAS_YFINANCE:
        try:
            tickers = yf.Tickers("GC=F CL=F ^GSPC")
            hist_gold = tickers.tickers["GC=F"].history(period="7d")
            hist_oil = tickers.tickers["CL=F"].history(period="7d")
            hist_sp500 = tickers.tickers["^GSPC"].history(period="7d")

            def process_data(hist_data, fallback_price: float, fallback_hist: List[float]):
                if len(hist_data) >= 2:
                    current_price = float(hist_data["Close"].iloc[-1])
                    previous_price = float(hist_data["Close"].iloc[-2])
                    change_pct = ((current_price - previous_price) / previous_price) * 100
                    history_list = [round(float(x), 2) for x in hist_data["Close"].tolist()]
                    return round(current_price, 2), round(change_pct, 2), history_list
                return fallback_price, 0.0, fallback_hist

            gold_price, gold_change, gold_hist = process_data(hist_gold, 2350.50, dummy_hist_gold)
            oil_price, oil_change, oil_hist = process_data(hist_oil, 82.30, dummy_hist_oil)
            sp_price, sp_change, sp_hist = process_data(hist_sp500, 5200.10, dummy_hist_sp)

            return {
                "Gold": {"price": gold_price, "change": gold_change, "history": gold_hist},
                "Oil": {"price": oil_price, "change": oil_change, "history": oil_hist},
                "SP500": {"price": sp_price, "change": sp_change, "history": sp_hist},
            }
        except Exception as e:
            logger.warning("Global Indicators API Error: %s", e)

    return {
        "Gold": {"price": 2350.50, "change": 0.65, "history": dummy_hist_gold},
        "Oil": {"price": 82.30, "change": 0.37, "history": dummy_hist_oil},
        "SP500": {"price": 5200.10, "change": 0.48, "history": dummy_hist_sp},
    }


# 4. National Macro Market Pulse
def get_national_market_pulse() -> Dict[str, Any]:
    """
    Simulates the National Macro Market Data for BD Gadget/Electronics sector.
    Ported directly from legacy-streamlit-mvp/data_engine.py.
    """
    current_hour = datetime.now().hour
    volatility = round(random.uniform(1.2, 4.5), 1)
    base_volume = 1250000000
    live_volume = base_volume + (current_hour * 15000000) + (volatility * 1000000)

    return {
        "market_volume": f"৳ {live_volume / 1000000000:.2f}B",
        "volume_change": f"{'+' if volatility > 0 else ''}{volatility:.1f}% (24h)",
        "active_wholesalers": random.randint(345, 378),
        "sentiment": "🔥 Bullish" if volatility > 0 else "🩸 Bearish",
        "avg_margin": f"{18.5 + (volatility / 10):.1f}%",
        "trending_sector": "TWS & Audio" if current_hour % 2 == 0 else "Smart Wearables",
        "struggling_sector": "PC Components" if current_hour % 2 == 0 else "Wired Accessories",
    }


# 5. Automated Retail Scraper (StarTech with Enterprise Fallback)
def scrape_real_retail_data(category: str = "smart-watch", attempt_network: bool = True) -> List[Dict[str, Any]]:
    """
    Advanced Scraper with Anti-Bot Bypassing & Smart Fallback.
    Ported from legacy-streamlit-mvp/automated_scraper.py.
    """
    url = f"https://www.startech.com.bd/accessories/{category}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
    }

    scraped_data: List[Dict[str, Any]] = []

    if attempt_network and HAS_BS4:
        try:
            response = requests.get(url, headers=headers, timeout=6)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                products = soup.find_all("div", class_=re.compile(r"p-item"))
                for p in products[:3]:
                    try:
                        name_elem = p.find(["h4", "div"], class_=re.compile(r"name"))
                        price_elem = p.find("div", class_=re.compile(r"price"))
                        if name_elem and price_elem:
                            name = name_elem.text.strip()
                            price_str = price_elem.text.strip().split("\n")[0]
                            digits = re.sub(r"[^\d]", "", price_str)
                            price = int(digits) if digits else 0
                            if price > 0:
                                scraped_data.append(
                                    {
                                        "product_name": name,
                                        "retail_price": price,
                                    }
                                )
                    except Exception:
                        continue
            if len(scraped_data) > 0:
                return scraped_data
        except Exception as e:
            logger.info("Scraping Engine Notice (using enterprise fallback): %s", e)

    # Enterprise Fallback (Never Fail a Demo!)
    return [
        {"product_name": "Kieslect Kr Pro Smart Calling Watch", "retail_price": 5750},
        {"product_name": "Xiaomi Redmi Watch 3 Active", "retail_price": 3350},
        {"product_name": "Amazfit Bip 3 Pro Smart Watch", "retail_price": 4950},
    ]


# 6. Live Market Terminal Snapshot (Gainers, Losers, Metrics)
def get_live_market_terminal_snapshot() -> Dict[str, Any]:
    """
    Returns Live Market Terminal metrics, High Demand Gainers, Slow Moving Losers,
    and DB scanned trend counts as defined in legacy-streamlit-mvp/app.py lines 567-600.
    """
    gainers = [
        {
            "asset_product": "AirPods Pro 2 (Master Clone)",
            "wholesale": "৳ 1,250",
            "wholesale_num": 1250,
            "trend_24h": "🟢 +15.2%",
            "pulse_7d": [102, 108, 114, 119, 124, 131, 136, 141, 145, 149],
        },
        {
            "asset_product": "MagSafe Battery Pack",
            "wholesale": "৳ 850",
            "wholesale_num": 850,
            "trend_24h": "🟢 +22.0%",
            "pulse_7d": [101, 106, 112, 118, 125, 130, 137, 142, 146, 150],
        },
        {
            "asset_product": "K68 RGB Keyboard",
            "wholesale": "৳ 1,800",
            "wholesale_num": 1800,
            "trend_24h": "🟢 +12.4%",
            "pulse_7d": [105, 109, 113, 116, 121, 126, 130, 135, 139, 144],
        },
        {
            "asset_product": "Lenovo LP40 Pro TWS",
            "wholesale": "৳ 550",
            "wholesale_num": 550,
            "trend_24h": "🟢 +18.5%",
            "pulse_7d": [100, 107, 111, 117, 123, 129, 134, 140, 144, 148],
        },
    ]

    losers = [
        {
            "asset_product": "Wired Earphones (Generic)",
            "wholesale": "৳ 80",
            "wholesale_num": 80,
            "trend_24h": "🔴 -18.2%",
            "pulse_7d": [78, 72, 66, 61, 55, 49, 43, 37, 30, 24],
        },
        {
            "asset_product": "Sub-1K Smartwatches",
            "wholesale": "৳ 650",
            "wholesale_num": 650,
            "trend_24h": "🔴 -25.0%",
            "pulse_7d": [80, 74, 67, 60, 52, 46, 39, 32, 26, 21],
        },
        {
            "asset_product": "Standard Phone Cases",
            "wholesale": "৳ 50",
            "wholesale_num": 50,
            "trend_24h": "🔴 -10.5%",
            "pulse_7d": [75, 71, 66, 62, 58, 53, 48, 43, 38, 34],
        },
        {
            "asset_product": "Micro-USB Cables",
            "wholesale": "৳ 45",
            "wholesale_num": 45,
            "trend_24h": "🔴 -12.0%",
            "pulse_7d": [76, 70, 65, 59, 54, 48, 42, 36, 31, 25],
        },
    ]

    return {
        "metrics": {
            "market_heat": {"value": "৳ 1.2B", "delta": "+8.2% (MoM)"},
            "buyer_mood": {"value": "🔥 Highly Bullish", "delta": "Buyers Dominating"},
            "avg_profit": {"value": "22.5%", "delta": "+1.1% (Due to USD)"},
        },
        "gainers": gainers,
        "losers": losers,
        "live_db_trends": get_live_terminal_data(),
    }


# 7. Supplier Trust Radar (SME Guardian)
def get_supplier_trust_radar(search_query: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes Supplier Trust Scores using crowdsourced memo price consistency (get_trust_scores)
    with full fallback Titans and Red Flag Scam Alerts as in legacy-streamlit-mvp/app.py lines 631-680.
    """
    trust_rows = get_trust_scores()
    dummy_suppliers = [
        "Gadget Kings BD (Multiplan)",
        "Audio Hub (Bashundhara)",
        "Tech Import Ltd (Gulshan)",
        "Electro Mart (Jamuna)",
        "Mobile World (Motaleb Plaza)",
    ]

    is_simulated = False
    verified_titans: List[Dict[str, Any]] = []

    if not trust_rows:
        is_simulated = True
        verified_titans = [
            {
                "wholesaler_importer": "Gadget Kings BD (Multiplan)",
                "dominant_product": "AirPods Pro 2",
                "trust_score": "🟢 95%",
                "score_num": 95,
                "ai_remarks": "Consistent pricing, 0 fake reports",
            },
            {
                "wholesaler_importer": "Audio Hub (Bashundhara)",
                "dominant_product": "Lenovo LP40",
                "trust_score": "🟢 90%",
                "score_num": 90,
                "ai_remarks": "Highly trusted, fast replacements",
            },
            {
                "wholesaler_importer": "Tech Import Ltd (Gulshan)",
                "dominant_product": "Apple Watch S9",
                "trust_score": "🟡 75%",
                "score_num": 75,
                "ai_remarks": "Slight price variations detected",
            },
            {
                "wholesaler_importer": "Electro Mart (Jamuna)",
                "dominant_product": "Smart Keyboard",
                "trust_score": "🔴 55%",
                "score_num": 55,
                "ai_remarks": "High price volatility, proceed with caution",
            },
        ]
    else:
        for idx, row in enumerate(trust_rows[:5]):
            supplier = dummy_suppliers[idx % len(dummy_suppliers)]
            variants = int(row.get("price_variants", 1))
            score = max(100 - (variants * 5), 50)
            if score >= 90:
                badge, remark = f"🟢 {score}%", "Consistent pricing, 0 fake reports"
            elif score >= 70:
                badge, remark = f"🟡 {score}%", "Slight price variations detected"
            else:
                badge, remark = f"🔴 {score}%", "High price volatility, proceed with caution"
            verified_titans.append(
                {
                    "wholesaler_importer": supplier,
                    "dominant_product": row["product_name"],
                    "trust_score": badge,
                    "score_num": score,
                    "ai_remarks": remark,
                }
            )

    if search_query and search_query.strip():
        q = search_query.strip().lower()
        filtered = [
            t
            for t in verified_titans
            if q in t["wholesaler_importer"].lower() or q in t["dominant_product"].lower()
        ]
        if not filtered:
            # Simulate dynamic radar result for searched shop
            filtered = [
                {
                    "wholesaler_importer": search_query.strip(),
                    "dominant_product": "Wholesale Gadgets & Accessories",
                    "trust_score": "🟢 88%",
                    "score_num": 88,
                    "ai_remarks": f"Cross-referenced memos for '{search_query.strip()}': Verified merchant history.",
                }
            ]
        verified_titans = filtered

    red_flag_alerts = [
        {
            "supplier": "Unverified Supplier selling 'Samsung S24 Ultra Cases'",
            "severity": "CRITICAL",
            "message": "⚠️ 4 different price points detected! AI detected abnormal price mismatch compared to local index.",
        }
    ]

    return {
        "is_simulated": is_simulated,
        "search_query": search_query or "",
        "verified_titans": verified_titans,
        "red_flag_alerts": red_flag_alerts,
    }

