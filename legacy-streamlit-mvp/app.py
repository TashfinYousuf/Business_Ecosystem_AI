import streamlit as st
import sqlite3
import pandas as pd
import random
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import os

from streamlit_option_menu import option_menu
from database import record_new_sale
from ai_engine import extract_sales_from_audio 
from streamlit_mic_recorder import mic_recorder
from database import init_db
init_db()

from data_engine import get_live_usd_rate, get_live_product_price, get_global_indicators
from ai_engine import get_market_insight, generate_idea_validation, extract_data_from_memo, generate_product_insight

from database import insert_price_data, get_price_history, register_user, verify_and_login_user, verify_account
from database import insert_memo_data, get_scanned_products, get_product_history, get_live_inventory, get_trust_scores
from database import get_live_terminal_data, get_trust_scores
from document_ai import extract_text_from_file, build_vector_database, analyze_report_with_ai

# --- Session Persistence Logic ---
def load_session():
    if os.path.exists("session_cache.json"):
        with open("session_cache.json", "r") as f:
            return json.load(f)
    return {"logged_in": False, "username": ""}

def save_session(logged_in, username):
    with open("session_cache.json", "w") as f:
        json.dump({"logged_in": logged_in, "username": username}, f)

def clear_session():
    if os.path.exists("session_cache.json"):
        os.remove("session_cache.json")

cached_session = load_session()
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = cached_session["logged_in"]
if "username" not in st.session_state:
    st.session_state["username"] = cached_session["username"]
if "show_verification" not in st.session_state:
    st.session_state["show_verification"] = False
if "temp_email" not in st.session_state:
    st.session_state["temp_email"] = ""
if "transitioning" not in st.session_state:
    st.session_state["transitioning"] = False

st.set_page_config(
    page_title="Business & Market AI Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# === SILICON VALLEY ENTERPRISE CSS (DARK MATTE) ===
# 🎨 Premium UI/UX Injector (Binance/TradingView Theme)
def inject_premium_ui():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Urbanist:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    :root {
        --wolf-teal: #14B8A6;
        --wolf-neon: #00FF9D;
        --silver: #F8FAFC;
    }

    /* 🔠 1. NUCLEAR HEADLINE OVERRIDES (Streamlit Specific) */
    .stMarkdown h1, .stMarkdown h1 > div, .stMarkdown h1 > div > span {
        font-family: 'Urbanist', sans-serif !important;
        font-size: 42px !important;
        font-weight: 800 !important;
        letter-spacing: -1px !important;
        background: -webkit-linear-gradient(45deg, var(--silver), var(--wolf-teal)) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-transform: uppercase;
        margin-bottom: 10px !important;
        line-height: 1.2 !important;
    }
    
    .stMarkdown h2, .stMarkdown h2 > div, .stMarkdown h2 > div > span {
        font-family: 'Urbanist', sans-serif !important;
        font-size: 32px !important;
        font-weight: 700 !important;
        color: var(--silver) !important;
        margin-bottom: 15px !important;
    }

    .stMarkdown h3, .stMarkdown h3 > div, .stMarkdown h3 > div > span {
        font-family: 'Urbanist', sans-serif !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        color: var(--wolf-teal) !important;
    }

    /* ✨ 2. SIDEBAR NAV HOVER (Deep Selector) */
    div[data-testid="stSidebarNav"] ul li div {
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        border-radius: 8px !important;
        margin: 2px 10px !important;
    }
    
    /* Hover Magic */
    div[data-testid="stSidebarNav"] ul li div:hover {
        transform: translateX(12px) scale(1.02) !important;
        background: linear-gradient(90deg, rgba(20, 184, 166, 0.15) 0%, transparent 100%) !important;
        border-left: 3px solid var(--wolf-neon) !important;
        box-shadow: -5px 0 15px rgba(0, 255, 157, 0.1) !important;
    }

    /* 👤 3. PREMIUM PROFILE POPOVER BUTTON */
    div[data-testid="stPopover"] > button {
        background: linear-gradient(135deg, rgba(20,184,166,0.15), rgba(0,255,157,0.05)) !important;
        border: 1px solid rgba(20,184,166,0.4) !important;
        border-radius: 30px !important; /* Fully rounded */
        padding: 5px 20px !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    
    div[data-testid="stPopover"] > button p {
        color: var(--silver) !important;
        font-weight: 700 !important;
        font-family: 'Urbanist', sans-serif !important;
        font-size: 16px !important;
    }

    div[data-testid="stPopover"] > button:hover {
        transform: translateY(-2px) !important;
        background: rgba(20,184,166,0.3) !important;
        box-shadow: 0 5px 20px rgba(20,184,166,0.3) !important;
    }

    /* 🛸 4. 3D FLOATING ALERTS */
    [data-testid="stAlert"] {
        background: rgba(19, 24, 34, 0.6) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        transition: transform 0.3s ease !important;
    }
    [data-testid="stAlert"]:hover {
        transform: translateY(-5px) !important;
    }
    </style>
    """, unsafe_allow_html=True)

inject_premium_ui()


if 'language' not in st.session_state:
    st.session_state['language'] = 'EN'


# ===============================
# 🌍 ENTERPRISE UI/UX DICTIONARY (Jargon-Free)
# ===============================
TEXT = {
    'EN': {
        'menu_terminal': 'Live Market 🔴',
        'menu_overview': 'Market Overview',
        'menu_radar': 'Trusted Suppliers 🛡️',
        'menu_analysis': 'Top Selling Items',
        'menu_risk': 'Safe Investment Guide',
        'menu_validator': 'Start New Business',
        'menu_scanner': 'Smart Memo Scanner',
        'menu_ledger': 'Order Inbox 📥',
        'menu_rag': 'Document Chat AI',
        
        'term_title': '⚡ Live Market Terminal',
        'term_cap': 'Track live wholesale prices and find the cheapest deals in the market.',
        'vol_title': 'Market Heat',
        'sentiment_title': 'Buyer Mood',
        'margin_title': 'Avg. Profit',
        'tab_gainers': '🔥 High Demand (Buy Now)',
        'tab_losers': '🩸 Slow Moving (Avoid)',
        'tab_arbitrage': '💸 Cheapest Deals',
        'btn_scrape': '🔄 Scan Live Market',
        'msg_success': '✅ Live Data Fetched!',
        
        'over_title': '🌍 Market Overview',
        'over_cap': 'Track your live stock and global import factors.',
        
        'scan_title': '📸 Auto Memo Entry',
        'scan_cap': 'Upload memos or voice notes. AI will update your stock automatically.',
        
        'sales_title': 'Customer Orders & Dues 🧾',
        'sales_cap': 'Record sales easily. AI tracks your cash, dues, and stock.',
        'sales_record': '📥 Order Inbox',
        'sales_info': 'Record voice or type: "Sold 5 AirPods to Tuhin Bhai at 600 tk."',
        'btn_process_sale': '🧠 Process Order',
        'sales_ledger': 'Customer Dues 📒'
    },

    'BN': {
        'menu_terminal': 'লাইভ মার্কেট 🔴',
        'menu_overview': 'মার্কেট ও স্টক',
        'menu_radar': 'নির্ভরযোগ্য সাপ্লায়ার 🛡️',
        'menu_analysis': 'বেস্ট সেলিং প্রোডাক্ট',
        'menu_risk': 'নিরাপদ ইনভেস্টমেন্ট',
        'menu_validator': 'নতুন ব্যবসার আইডিয়া',
        'menu_scanner': 'অটো মেমো এন্ট্রি',
        'menu_ledger': 'অর্ডার ইনবক্স 📥',
        'menu_rag': 'ডকুমেন্ট এআই (PDF)',
        
        'term_title': '⚡ লাইভ মার্কেট টার্মিনাল',
        'term_cap': 'পাইকারি বাজারের লাইভ দাম এবং সবচেয়ে সস্তা ডিলগুলো খুঁজুন।',
        'vol_title': 'মার্কেটের অবস্থা',
        'sentiment_title': 'ক্রেতাদের মুড',
        'margin_title': 'গড় লাভ',
        'tab_gainers': '🔥 প্রচুর চাহিদা (কিনুন)',
        'tab_losers': '🩸 বিক্রি কম (এড়িয়ে চলুন)',
        'tab_arbitrage': '💸 সস্তা ডিল (অফার)',
        'btn_scrape': '🔄 লাইভ মার্কেট স্ক্যান করুন',
        'msg_success': '✅ ডাটা আপডেট হয়েছে!',
        
        'over_title': '🌍 মার্কেট ও স্টক ওভারভিউ',
        'over_cap': 'আপনার বর্তমান স্টক এবং গ্লোবাল ইমপোর্ট রেট ট্র্যাক করুন।',
        
        'scan_title': '📸 অটো মেমো ও স্টক এন্ট্রি',
        'scan_cap': 'মেমো বা ভয়েস দিন, এআই অটোমেটিক আপনার স্টকে মাল তুলে দিবে।',
        
        'sales_title': 'অর্ডার এবং কাস্টমার খাতা 🧾',
        'sales_cap': 'সহজে বেচাকেনা রেকর্ড করুন। এআই আপনার ক্যাশ এবং বাকি হিসাব রাখবে।',
        'sales_record': '📥 অর্ডার ইনবক্স',
        'sales_info': 'ভয়েস দিন বা লিখুন: "তুহিন ভাইকে ৬০০ টাকা করে ৫টা এয়ারপডস দিলাম।"',
        'btn_process_sale': '🧠 অর্ডার প্রসেস করুন',
        'sales_ledger': 'কাস্টমারের বাকি 📒'
    }
}

t = TEXT[st.session_state['language']] 



# 🚨 DB Fallback: Ultimate Auto-Fix (All Missing Columns)
try:
    conn = sqlite3.connect('market_data.db')
    c = conn.cursor()
    
    # টেবিল না থাকলে ফোন এবং is_verified সহ একেবারে পারফেক্টলি বানাবে
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  email TEXT UNIQUE, 
                  phone TEXT,
                  password_hash TEXT,
                  is_verified INTEGER DEFAULT 0)''')
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    except:
        pass # phone কলাম থাকলে ইগনোর করবে
        
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
    except:
        pass # is_verified কলাম থাকলে ইগনোর করবে
        
    conn.commit()
    conn.close()
except Exception as e:
    pass

# =====================================================================
# AUTHENTICATION UI
# =====================================================================
if not st.session_state["logged_in"]:
    if st.session_state["transitioning"]:
        st.markdown(f"""
            <div class="center-popup">
                <h2 style="color: #00E676;">Welcome back, {st.session_state['username']}!</h2>
                <p style="color: #A0A0B0;">Preparing your personalized dashboard...</p>
                <div style="margin-top: 20px;"><img src="https://i.gifer.com/ZKZg.gif" width="40px"></div>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(2)
        st.session_state["transitioning"] = False
        st.rerun()
    else:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align: center; color: white;'>📊 AI Business Assistant</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #A0A0B0; margin-bottom: 30px;'>Sign in to continue to your workspace</p>", unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["Log In", "Create Account"])
            with tab1:
                with st.form("login_form", clear_on_submit=False):
                    log_email = st.text_input("Email Address", placeholder="e.g., alex@ai.com")
                    log_pass = st.text_input("Password", type="password", placeholder="••••••••")
                    submit_login = st.form_submit_button("Access Dashboard", use_container_width=True)
                    if submit_login:
                        res = verify_and_login_user(log_email, log_pass)
                        if res["status"] == "success":
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = res["username"]
                            save_session(True, res["username"])
                            st.session_state["transitioning"] = True 
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please try again.")
            with tab2:
                if not st.session_state["show_verification"]:
                    with st.form("signup_form"):
                        reg_name = st.text_input("Full Name", placeholder="Alex Doe")
                        reg_email = st.text_input("Email", placeholder="alex@ai.com")
                        reg_phone = st.text_input("Phone Number", placeholder="+8801...")
                        reg_pass = st.text_input("Create Password", type="password")
                        submit_signup = st.form_submit_button("Create AI Account", use_container_width=True)
                        if submit_signup:
                            if reg_name and reg_email and reg_pass:
                                is_success = register_user(reg_name, reg_email, reg_phone, reg_pass)
                                if is_success:
                                    st.session_state["show_verification"] = True
                                    st.session_state["temp_email"] = reg_email
                                    st.rerun()
                                else:
                                    st.error("Email already registered. Try logging in.")
                            else:
                                st.warning("Please fill all required fields.")
                else:
                    st.info(f"An OTP has been sent to **{st.session_state['temp_email']}**")
                    with st.form("verify_form"):
                        otp = st.text_input("Enter 4-digit OTP (Type 1234 for testing)", max_chars=4)
                        verify_btn = st.form_submit_button("Verify & Login", use_container_width=True)
                        if verify_btn:
                            if otp == "1234":
                                verify_account(st.session_state["temp_email"])
                                st.session_state["logged_in"] = True
                                st.session_state["username"] = "New User"
                                save_session(True, "New User")
                                st.session_state["transitioning"] = True
                                st.rerun()
                            else:
                                st.error("Invalid OTP.")

# =====================================================================
# MAIN DASHBOARD
# =====================================================================
else:
    col_space, col_profile = st.columns([9, 1.2])
    with col_profile:
        with st.popover("👤 Profile"):
            st.markdown(f"**{st.session_state.get('username', 'User')}**")
            st.caption("Founder / Admin")
            st.divider()
            st.markdown("**Language / ভাষা**")
            lang_choice = st.radio("Language", options=['EN', 'BN'], index=0 if st.session_state['language'] == 'EN' else 1, horizontal=True, label_visibility="collapsed")
            if lang_choice != st.session_state['language']:
                st.session_state['language'] = lang_choice
                st.rerun() 
            st.divider()
            if st.button("🚪 Log Out", type="primary", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state["logged_in"] = False
                clear_session()
                st.rerun()
            
    st.markdown("---")

    # 5. Gorgeous & Smooth Sidebar Navigation
    with st.sidebar:
        # --- Clickable Trade Wolf Logo ---
        import base64
        def get_img_as_b64(file_path):
            try:
                with open(file_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            except:
                return ""
        
        img_b64 = get_img_as_b64("logo.png")
        
        st.markdown(f'''
            <a href="?" target="_self" style="text-decoration:none;">
                <div style="text-align:center; padding-bottom: 20px; transition: transform 0.4s ease;" 
                     onmouseover="this.style.transform='scale(1.08) translateY(-5px)'" 
                     onmouseout="this.style.transform='scale(1) translateY(0)'">
                    <img src="data:image/png;base64,{img_b64}" width="90%" style="border-radius: 16px; filter: drop-shadow(0 10px 20px rgba(20,184,166,0.3));" />
                </div>
            </a>
        ''', unsafe_allow_html=True)
        
        st.markdown("<div style='text-align: center; margin-top: -20px; margin-bottom: 15px;'><b style='color: #14B8A6; font-size: 14px; letter-spacing: 1px;'>FOUNDER WORKSPACE</b></div>", unsafe_allow_html=True)


        # Get the current language dictionary
        lang = st.session_state['language']
        t = TEXT[lang]

        menu = option_menu(
            menu_title=None,
            options=[t['menu_terminal'], t['menu_overview'], t['menu_radar'], t['menu_analysis'], t['menu_risk'], t['menu_validator'], t['menu_scanner'], t['menu_ledger'], t['menu_rag']], 
            icons=["bar-chart-line-fill", "activity", "shield-check", "box-seam", "wallet2", "lightbulb", "upc-scan", "whatsapp", "file-earmark-text"], 
            menu_icon="cast", 
            default_index=0, 
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#4CAF50", "font-size": "18px"}, 
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "color": "#e0e0e0"},
                "nav-link-selected": {"background-color": "rgba(76, 175, 80, 0.2)", "color": "#ffffff", "border-left": "3px solid #4CAF50"},
            }
        )

    # ====================================================================
    # 1. SMART MEMO SCANNER (ONLY IMAGE)
    # ====================================================================
    if menu == t['menu_scanner']:
        st.subheader(t['scan_title'])
        st.caption(t['scan_cap'])
        st.markdown("---")
        
        scan_tab_img, scan_tab_voice, scan_tab_text = st.tabs(["📸 Scan Image Memo", "🎙️ Voice Purchase", "💬 Text Purchase"])
        
        with scan_tab_img:
            uploaded_image = st.file_uploader("Upload Wholesale Memo (JPG, PNG)", type=["jpg", "jpeg", "png"], key="scanner_img_up")
            if uploaded_image is not None:
                st.image(uploaded_image, caption="Uploaded Memo", use_container_width=True)
                if st.button("🔍 Extract & Calculate Ledger", type="primary", use_container_width=True):
                    with st.spinner("AI মেমোর ছবি স্ক্যান করছে..."):
                        from ai_engine import extract_data_from_memo
                        import json
                        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
                        try:
                            image_bytes = uploaded_image.getvalue()
                            extracted_json_str = extract_data_from_memo(image_bytes, GEMINI_API_KEY)
                            st.session_state['temp_purchase'] = json.loads(extracted_json_str)
                        except Exception as e:
                            st.error(f"Image Parsing Error: {e}")
                            

        # --- TAB 2: VOICE PURCHASE (Scanner) ---
        with scan_tab_voice:
            scan_audio_file = st.file_uploader("Upload Purchase Audio File", type=["mp3", "wav", "m4a"], key="scan_audio_file_up")
            
            from streamlit_mic_recorder import mic_recorder
            scan_audio = mic_recorder(start_prompt="🎤 Or Record Purchase Live", stop_prompt="🛑 Stop", key="scan_voice")
            
            p_audio_bytes = None
            if scan_audio_file is not None:
                p_audio_bytes = scan_audio_file.getvalue()
            elif scan_audio is not None:
                # Extract 'bytes' directly
                p_audio_bytes = scan_audio['bytes']
                
            if p_audio_bytes is not None and st.button("🧠 Process Voice Purchase", type="primary", use_container_width=True):
                with st.spinner("AI পাইকারি ক্রয়ের অডিও অ্যানালাইসিস করছে..."):

                    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
                    try:
                        ai_json = extract_sales_from_audio(p_audio_bytes, "audio/wav", GEMINI_API_KEY)
                        st.session_state['temp_purchase'] = json.loads(ai_json)
                    except Exception as e:
                        st.error(f"Voice Stock Extraction Error: {e}")


        # --- TAB 3: TEXT PURCHASE (Scanner) ---
        with scan_tab_text:
            scan_text = st.text_area("Paste bulk purchase text message:", height=100, key="scan_text_area")
            if scan_text and st.button("🧠 Process Text Purchase", type="primary", use_container_width=True):
                with st.spinner("AI টেক্সটকে স্টকে কনভার্ট করছে..."):
            
                    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
                    prompt = f'''Extract wholesale purchase text: "{scan_text}". Return JSON: {{"product_name": "...", "unit_price": X, "quantity": X}}'''
            
                    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}}
                    response = requests.post(url, json=payload).json()

                    # 🚀 Enterprise Retry Mechanism (Exponential Backoff)
                    max_retries = 3
                    success = False
                    
                    for attempt in range(max_retries):
                        try:
                            response = requests.post(url, json=payload)
                            
                            if response.status_code == 200:
                                ai_json = response.json()['candidates'][0]['content']['parts'][0]['text']
                                st.session_state['temp_order'] = json.loads(ai_json)
                                st.session_state['order_source'] = 'ledger'
                                success = True
                                break # সাকসেস হলে লুপ থেকে বের হয়ে যাবে
                            
                            elif response.status_code == 429:
                                # 429 আসলে ইউজারকে না দেখিয়ে ব্যাকগ্রাউন্ডে ওয়েট করবে
                                wait_time = 2 ** attempt # ২, ৪, ৮ সেকেন্ড করে ওয়েট করবে
                                st.warning(f"সার্ভার একটু বিজি.. AI অটোমেটিক আবার ট্রাই করছে... ({attempt + 1}/{max_retries})")
                                time.sleep(wait_time)
                            else:
                                st.error(f"API Error: {response.text}")
                                break
                        except Exception as e:
                            st.error(f"Network Error: {e}")
                            break
                    
                    if not success:
                        st.error("⚠️ সার্ভার অতিরিক্ত ব্যস্ত। দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন বা অন্য কোনো ইনপুট মেথড ব্যবহার করুন।")

        # --- 🛠️ INVENTORY PREVIEW & EDIT ACTION BOX BEFORE DB SAVE ---
        if 'temp_purchase' in st.session_state:
            st.markdown("---")
            st.markdown("### 📦 Review & Edit Incoming Inventory Stock")
            st.caption("স্টক ডেটাবেসে পুশ করার আগে আইটেমের নাম, পাইকারি রেট এবং কোয়ান্টিটি চেক বা এডিট করে নিন।")
            
            p_data = st.session_state['temp_purchase']
            items_list = p_data.get("items", [])
            
            if items_list:
                # ম্যাসন বা ব্যাচ ইনপুট ইন্টারেক্টিভ টেবিল এডিটর
                edited_items = st.data_editor(items_list, num_rows="dynamic", use_container_width=True, key="memo_editor_grid")
                if st.button("💾 Commit Whole Invoice to Inventory", type="primary", use_container_width=True):
                    conn = sqlite3.connect('market_data.db')
                    c = conn.cursor()
                    c.execute("CREATE TABLE IF NOT EXISTS memo_tracker (id INTEGER PRIMARY KEY, product_name TEXT, price REAL, status TEXT, scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                    for item in edited_items:
                        name = item.get("product_name", "Unknown")
                        price = float(item.get("unit_price", 0))
                        qty = int(item.get("quantity", 1))
                        for _ in range(qty):
                            c.execute("INSERT INTO memo_tracker (product_name, price, status) VALUES (?, ?, ?)", (name, price, "Stock Added"))
                    conn.commit()
                    conn.close()
                    st.success("✅ পুরো মেমোর স্টক ইনভেন্টরিতে সেভ করা হয়েছে!")
                    del st.session_state['temp_purchase']
                    st.rerun()
            else:
                name_val = p_data.get("product_name", p_data.get("item_name", "Unknown Asset"))
                price_val = float(p_data.get("unit_price", 0))
                qty_val = int(p_data.get("quantity", 1))
                
                edit_p_name = st.text_input("Product Stock Name:", value=name_val)
                edit_p_price = st.number_input("Wholesale Unit Price (৳):", min_value=0.0, value=price_val)
                edit_p_qty = st.number_input("Wholesale Quantity:", min_value=1, value=qty_val)
                
                sb1, sb2 = st.columns(2)
                with sb1:
                    if st.button("💾 Save Stock to Inventory", type="primary", use_container_width=True):
                        conn = sqlite3.connect('market_data.db')
                        c = conn.cursor()
                        c.execute("CREATE TABLE IF NOT EXISTS memo_tracker (id INTEGER PRIMARY KEY, product_name TEXT, price REAL, status TEXT, scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                        for _ in range(int(edit_p_qty)):
                            c.execute("INSERT INTO memo_tracker (product_name, price, status) VALUES (?, ?, ?)", (edit_p_name, edit_p_price, "Stock Added"))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ ইনভেন্টরিতে {edit_p_qty} পিস {edit_p_name} যোগ করা হয়েছে!")
                        del st.session_state['temp_purchase']
                        st.rerun()
                with sb2:
                    if st.button("🗑️ Discard Entry", use_container_width=True):
                        del st.session_state['temp_purchase']
                        st.warning("স্টক এন্ট্রি বাতিল করা হয়েছে।")
                        st.rerun()

    # ====================================================================
    # 2. LIVE TERMINAL 🔴
    # ====================================================================
    elif menu == t['menu_terminal']:
        st.subheader(t['term_title'])
        st.caption(t['term_cap'])
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric(t['vol_title'], "৳ 1.2B", "+8.2% (MoM)")
        col2.metric(t['sentiment_title'], "🔥 Highly Bullish", "Buyers Dominating")
        col3.metric(t['margin_title'], "22.5%", "+1.1% (Due to USD)")
        
        st.markdown("<br>", unsafe_allow_html=True)
        tab_gainers, tab_losers, tab_arbitrage = st.tabs([t['tab_gainers'], t['tab_losers'], t['tab_arbitrage']])
        
        with tab_gainers:
            st.markdown("<br>", unsafe_allow_html=True)
            hot_data = pd.DataFrame({
                "Asset / Product": ["AirPods Pro 2 (Master Clone)", "MagSafe Battery Pack", "K68 RGB Keyboard", "Lenovo LP40 Pro TWS"],
                "Wholesale": ["৳ 1,250", "৳ 850", "৳ 1,800", "৳ 550"],
                "24h Trend": ["🟢 +15.2%", "🟢 +22.0%", "🟢 +12.4%", "🟢 +18.5%"],
                "7-Day Pulse": [[random.randint(100, 150) for _ in range(10)] for _ in range(4)]
            })
            for i in range(4): hot_data.at[i, "7-Day Pulse"] = sorted(hot_data.at[i, "7-Day Pulse"])
            st.dataframe(hot_data, column_config={"Asset / Product": st.column_config.TextColumn("Asset / Product", width="medium"), "7-Day Pulse": st.column_config.LineChartColumn("7-Day Pulse", y_min=50, y_max=200, width="medium")}, hide_index=True, use_container_width=True)

        with tab_losers:
            st.markdown("<br>", unsafe_allow_html=True)
            cold_data = pd.DataFrame({
                "Asset / Product": ["Wired Earphones (Generic)", "Sub-1K Smartwatches", "Standard Phone Cases", "Micro-USB Cables"],
                "Wholesale": ["৳ 80", "৳ 650", "৳ 50", "৳ 45"],
                "24h Trend": ["🔴 -18.2%", "🔴 -25.0%", "🔴 -10.5%", "🔴 -12.0%"],
                "7-Day Pulse": [[random.randint(20, 80) for _ in range(10)] for _ in range(4)]
            })
            for i in range(4): cold_data.at[i, "7-Day Pulse"] = sorted(cold_data.at[i, "7-Day Pulse"], reverse=True)
            st.dataframe(cold_data, column_config={"Asset / Product": st.column_config.TextColumn("Asset / Product", width="medium"), "7-Day Pulse": st.column_config.LineChartColumn("7-Day Pulse", y_min=0, y_max=100, width="medium")}, hide_index=True, use_container_width=True)

        with tab_arbitrage:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🕸️ Live Scraper & AI Arbitrage")
            st.caption("Scraping real-time retail prices from BD E-commerce (Star Tech) and matching with AI predictive logic.")
            if st.button(t['btn_scrape'], type="primary"):
                with st.spinner("Scraping Star Tech servers & running AI Quant Models..."):
                    from automated_scraper import scrape_real_retail_data
                    from ai_engine import generate_math_prediction
                    import time
                    real_retail_data = scrape_real_retail_data(category="smart-watch")
                    if real_retail_data:
                        assumed_wholesale_discount = 0.65 
                        st.success(t['msg_success'])
                        for item in real_retail_data:
                            retail_bdt = item['retail_price']
                            wholesale_bdt = int(retail_bdt * assumed_wholesale_discount)
                            GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
                            prediction = generate_math_prediction(item['product_name'], wholesale_bdt, retail_bdt, GEMINI_API_KEY)
                            with st.expander(f"📊 {item['product_name']} | Retail: ৳{retail_bdt}"):
                                c1, c2 = st.columns(2)
                                c1.metric("Live Retail (Scraped)", f"৳{retail_bdt}")
                                c2.metric("Est. Wholesale", f"৳{wholesale_bdt}")
                                st.markdown("#### 🧠 AI Quant Analysis")
                                st.markdown(prediction)
                    else:
                        st.error("Failed to scrape data. Target website might have changed its layout.")

    # ====================================================================
    # 3. TRUST RADAR (WITH BULLETPROOF FALLBACK)
    # ====================================================================
    elif menu == t['menu_radar']:
        st.subheader("🛡️ Supplier Trust Radar (SME Guardian)")
        st.markdown("We use AI and crowdsourced memo analysis to detect honest suppliers and flag market manipulators based on price consistency.")
        st.markdown("---")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_supplier = st.text_input("🔍 Search Wholesaler Name or Location (e.g., 'Multiplan Shop 302')")
        with search_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("Search Radar", type="primary", use_container_width=True)
        
        if search_supplier:
            with st.spinner("Analyzing cross-referenced memos and merchant history..."):
                time.sleep(1)
                st.warning("Feature in Alpha: Simulating radar results for demonstration.")
        
        st.markdown("#### 🏆 Top Verified Titans (Safe to Trade)")
        
        # Safe Data Fetching with Fallback
        try:
            trust_df = get_trust_scores()
        except Exception:
            trust_df = pd.DataFrame()
            
        if trust_df is None or trust_df.empty or 'price_variants' not in trust_df.columns:
            # BEAUTIFUL FALLBACK DATA IF DB IS EMPTY (No more blank screens)
            st.info("💡 Note: Displaying simulated market trust scores because your scanner database is empty.")
            display_data = [
                {"Wholesaler / Importer": "Gadget Kings BD (Multiplan)", "Dominant Product": "AirPods Pro 2", "Trust Score": "🟢 95%", "AI Remarks": "Consistent pricing, 0 fake reports"},
                {"Wholesaler / Importer": "Audio Hub (Bashundhara)", "Dominant Product": "Lenovo LP40", "Trust Score": "🟢 90%", "AI Remarks": "Highly trusted, fast replacements"},
                {"Wholesaler / Importer": "Tech Import Ltd (Gulshan)", "Dominant Product": "Apple Watch S9", "Trust Score": "🟡 75%", "AI Remarks": "Slight price variations detected"},
                {"Wholesaler / Importer": "Electro Mart (Jamuna)", "Dominant Product": "Smart Keyboard", "Trust Score": "🔴 55%", "AI Remarks": "High price volatility, proceed with caution"}
            ]
            st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)
            st.markdown("#### 🚨 Red Flag / Scam Alerts")
            st.error("**Unverified Supplier selling 'Samsung S24 Ultra Cases'** - ⚠️ 4 different price points detected! AI detected abnormal price mismatch compared to local index.")
        else:
            # Actual DB Logic
            dummy_suppliers = ["Gadget Kings BD (Multiplan)", "Audio Hub (Bashundhara)", "Tech Import Ltd (Gulshan)", "Electro Mart (Jamuna)", "Mobile World"]
            display_data = []
            for idx, (_, row) in enumerate(trust_df.head(5).iterrows()):
                supplier = dummy_suppliers[idx % len(dummy_suppliers)]
                variants = int(row.get('price_variants', 1)) if not pd.isna(row.get('price_variants')) else 1
                score = max(100 - (variants * 5), 50) 
                if score >= 90: trust_badge, remark = f"🟢 {score}%", "Consistent pricing, 0 fake reports"
                elif score >= 70: trust_badge, remark = f"🟡 {score}%", "Slight price variations detected"
                else: trust_badge, remark = f"🔴 {score}%", "High price volatility, proceed with caution"
                display_data.append({"Wholesaler / Importer": supplier, "Dominant Product": row['product_name'], "Trust Score": trust_badge, "AI Remarks": remark})
            st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)

    # ====================================================================
    # 4. MARKET OVERVIEW (WITH BULLETPROOF FALLBACK)
    # ====================================================================
    elif menu == t['menu_overview']:
        st.subheader("🌍 Macro & Micro Market Overview")
        st.caption("Live national market pulse combined with global economic indicators and your private asset wallet.")
        
        def draw_sparkline(history, delta):
            color = "#00E676" if delta >= 0 else "#FF5252"
            fig = go.Figure(go.Scatter(y=history, mode='lines', line=dict(color=color, width=3)))
            fig.update_layout(height=35, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False, hovermode=False)
            return fig
        
        from data_engine import get_national_market_pulse
        nat_pulse = get_national_market_pulse()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📊 National Sector Pulse & Volume")
        col1, col2, col3 = st.columns(3)
        col1.metric("24h Nat. Trade Volume", nat_pulse["market_volume"], nat_pulse["volume_change"])
        col2.metric("Market Sentiment", nat_pulse["sentiment"], f"Avg Margin: {nat_pulse['avg_margin']}")
        try:
            usd_data = get_live_usd_rate()
            col3.metric(label="Live USD/BDT Rate", value=f"৳ {usd_data['price']}", delta=f"{usd_data['change']}%")
            if 'history' in usd_data:
                col3.plotly_chart(draw_sparkline(usd_data['history'], usd_data['change']), use_container_width=True, config={'displayModeBar': False})
        except Exception: pass

        h_col1, h_col2, h_col3 = st.columns(3)
        h_col1.metric("🔥 Hottest Sector", nat_pulse["trending_sector"], "High Demand")
        h_col2.metric("🩸 Struggling Sector", nat_pulse["struggling_sector"], "Saturated", delta_color="inverse")
        h_col3.metric("Active Wholesalers Tracked", f"{nat_pulse['active_wholesalers']} Hubs", "Live Network")
        st.markdown("---")
        
        st.markdown("#### 🌍 Global Economic Indicators (Import Factors)")
        try:
            global_data = get_global_indicators()
            if global_data:
                gcol1, gcol2, gcol3 = st.columns(3)
                gcol1.metric(label="Gold (per oz)", value=f"${global_data['Gold']['price']:,}", delta=f"{global_data['Gold']['change']}%")
                gcol1.plotly_chart(draw_sparkline(global_data['Gold']['history'], global_data['Gold']['change']), use_container_width=True, config={'displayModeBar': False}, key="gold_spark")
                gcol2.metric(label="Crude Oil (per bbl)", value=f"${global_data['Oil']['price']}", delta=f"{global_data['Oil']['change']}%")
                gcol2.plotly_chart(draw_sparkline(global_data['Oil']['history'], global_data['Oil']['change']), use_container_width=True, config={'displayModeBar': False}, key="oil_spark")
                gcol3.metric(label="S&P 500 Index", value=f"{global_data['SP500']['price']:,}", delta=f"{global_data['SP500']['change']}%")
                gcol3.plotly_chart(draw_sparkline(global_data['SP500']['history'], global_data['SP500']['change']), use_container_width=True, config={'displayModeBar': False}, key="sp500_spark")
            else: st.warning("Fetching Global Market Data...")
        except Exception: st.warning("Global API is resting. Fetching soon...")
        st.markdown("---")
        
        st.markdown("#### 💼 Live Local Inventory (Private Wallet)")
        try:
            import sqlite3
            conn = sqlite3.connect('market_data.db')
            
            # টেবিল না থাকলে বানিয়ে নিবে (Error এড়ানোর জন্য)
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS memo_tracker (id INTEGER PRIMARY KEY, product_name TEXT, price REAL, status TEXT, scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            c.execute("CREATE TABLE IF NOT EXISTS sales_ledger (id INTEGER PRIMARY KEY, customer TEXT, item TEXT, qty INTEGER, unit_price REAL, total_bill REAL, paid REAL, due REAL, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            
            df_memos = pd.read_sql_query("SELECT product_name, price, status, scan_date FROM memo_tracker", conn)
            df_sales = pd.read_sql_query("SELECT item as product_name, unit_price as price, 'From Sales Ledger' as status, date as scan_date FROM sales_ledger", conn)
            conn.close()
            
            inventory_df = pd.concat([df_memos, df_sales]).drop_duplicates(subset=['product_name'], keep='last')
            
            if inventory_df.empty:
                st.info("📭 Your asset wallet is empty. Scan wholesale memos or record a sale to build inventory.")
            else:
                inventory_df.rename(columns={'product_name': 'Asset / Product', 'price': 'Current Wholesale', 'status': 'Stock Status', 'scan_date': 'Last Updated'}, inplace=True)
                st.dataframe(inventory_df, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"Database sync error: {e}")



    # ====================================================================
    # 5. PRODUCT ANALYSIS & PROACTIVE ALERTS (THE FLYWHEEL)
    # ====================================================================
    elif menu == t['menu_analysis']:
        st.subheader("📦 AI Product & Trend Analytics")
        st.caption("Track your personal performance, compare with the community, and get AI-driven alerts.")
        st.markdown("---")

        try:
            conn = sqlite3.connect('market_data.db')
            df = pd.read_sql_query("SELECT item, qty, total_bill, unit_price FROM sales_ledger", conn)
            due_df = pd.read_sql_query("SELECT due FROM sales_ledger", conn)
            conn.close()
        except:
            df = pd.DataFrame()
            due_df = pd.DataFrame()

        # 🚀 3 Tabs including the new Proactive Alerts
        tab_personal, tab_community, tab_alerts = st.tabs(["📊 My Ledger Analytics", "🌐 Community Trends", "🔔 Proactive AI Alerts"])
        
        # --- TAB 1: YOUR PERSONAL LEDGER ---
        with tab_personal:
            if not df.empty:
                top_items = df.groupby('item').agg({'qty': 'sum', 'total_bill': 'sum'}).reset_index()
                top_items = top_items.sort_values(by='qty', ascending=False)
                
                col1, col2 = st.columns(2)
                best_seller = top_items.iloc[0]['item']
                col1.metric("🔥 Top Selling Asset (Yours)", best_seller, "Highest Volume")
                col2.metric("Total Units Sold", f"{top_items['qty'].sum()} Units", "Live Data")
                
                st.markdown("#### 📊 Item-wise Market Demand (Your Shop)")
                top_items.rename(columns={'item': 'Product Name', 'qty': 'Units Sold', 'total_bill': 'Revenue Generated'}, inplace=True)
                top_items['Revenue Generated'] = top_items['Revenue Generated'].apply(lambda x: f"৳{x:,.0f}")
                st.dataframe(top_items, hide_index=True, use_container_width=True)
            else:
                st.warning("⚠️ No personal sales data found. Please add sales in 'WhatsApp Sales Ledger' first.")

        # --- TAB 2: COMMUNITY INTELLIGENCE ---

        with tab_community:
            st.markdown("#### 🧠 National Crowd-Sourced Trends")
            st.caption("Anonymized trend analysis from the entire Trade Wolf merchant network.")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Trending Nationwide", "AirPods Pro 2", "+24% Demand")
            c2.metric("Market Saturated", "Wired Earphones", "-15% Demand", delta_color="inverse")
            c3.metric("Upcoming Hype", "Smart Rings", "+45% Search Volume")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### ⚖️ Price Benchmark (You vs Market)")
            
            user_prices = {}
            if not df.empty:
                avg_prices = df.groupby('item')['unit_price'].mean().to_dict()
                user_prices = {k: int(v) for k, v in avg_prices.items()}
            
            market_db = {
                "AirPods Pro 2": {"avg": 1350, "trend": "🔥 High Demand"},
                "Apple Watch S9": {"avg": 2500, "trend": "⚖️ Stable"},
                "Lenovo LP40 TWS": {"avg": 600, "trend": "🔥 High Demand"},
            }
            
            benchmark_data = []
            items_to_show = list(user_prices.keys()) if user_prices else list(market_db.keys())
            
            for item in items_to_show:
                market_avg = market_db.get(item, {}).get("avg", random.randint(800, 3500))
                market_trend = market_db.get(item, {}).get("trend", "⚖️ Stable")
                my_avg = user_prices.get(item, 0)
                
                status = "N/A"
                if my_avg > 0:
                    if my_avg > market_avg: status = "🟢 Selling Higher (Good Margin)"
                    elif my_avg < market_avg: status = "🔴 Underselling (Losing Margin)"
                    else: status = "⚪ Average Market Price"
                
                benchmark_data.append({
                    "Product": item,
                    "National Avg. Retail": f"৳{market_avg:,}",
                    "Your Avg. Retail": f"৳{my_avg:,}" if my_avg > 0 else "No Sales Yet",
                    "AI Verdict": status,
                    "National Demand": market_trend
                })
                
            st.dataframe(pd.DataFrame(benchmark_data), hide_index=True, use_container_width=True)

        # --- TAB 3: PROACTIVE AI ALERTS (THE DATA FLYWHEEL ENGINE) ---
        with tab_alerts:
            st.markdown("#### 🤖 Trade Wolf Copilot (Live Business Advice)")
            st.caption("AI reads your inventory velocity, cross-matches with community trends, and triggers warnings.")
            st.markdown("<br>", unsafe_allow_html=True)
            
            try:
                conn = sqlite3.connect('market_data.db')
                # কেনা মালের ডাটা (Memo Tracker)
                df_buy = pd.read_sql_query("SELECT product_name, COUNT(*) as total_bought FROM memo_tracker GROUP BY product_name", conn)
                # বেচা মালের ডাটা (Sales Ledger)
                df_sell = pd.read_sql_query("SELECT item as product_name, SUM(qty) as total_sold FROM sales_ledger GROUP BY item", conn)
                conn.close()
                
                # দুটি ডাটাফ্রেম মার্চ করে নিখুঁত স্টক বের করা
                if not df_buy.empty or not df_sell.empty:
                    if df_buy.empty: df_buy = pd.DataFrame(columns=['product_name', 'total_bought'])
                    if df_sell.empty: df_sell = pd.DataFrame(columns=['product_name', 'total_sold'])
                    
                    inv_merge = pd.merge(df_buy, df_sell, on='product_name', how='outer').fillna(0)
                    inv_merge['Current_Stock'] = inv_merge['total_bought'] - inv_merge['total_sold']
                    
                    # কম স্টক আছে এমন প্রোডাক্ট ফিল্টার করা (যেমন: < ৩ পিস)
                    low_stock_items = inv_merge[inv_merge['Current_Stock'] <= 3]
                    
                    # মার্কেট ডিমান্ড ডাটাবেস (Crowd Trends-এর সাথে ম্যাচিং লজিক)
                    market_hype = {"AirPods Pro 2": "High", "Apple Watch S9": "Stable", "Lenovo LP40 TWS": "High"}
                    
                    alert_triggered = False
                    
                    for _, row in low_stock_items.iterrows():
                        p_name = row['product_name']
                        p_stock = int(row['Current_Stock'])
                        demand = market_hype.get(p_name, "Stable")
                        
                        # 🚨 কন্ডিশনাল এলার্ট জেনারেশন (Flywheel Hook)
                        if demand == "High" or p_stock <= 0:
                            alert_triggered = True
                            st.warning(f"📉 **Stockout Risk & High Demand:** Your stock for **'{p_name}'** is critically low ({p_stock} pcs remaining). Nationwide community demand is spiking up! Suppliers might increase wholesale prices soon.\n\n👉 **AI Action Advice:** Restock at least 15-20 units within 24 hours to capture current retail market margins.")
                    
                    # ক্যাশফ্লো এবং লিকুইডিটি অ্যালার্ট (Sales Ledger এর Dues এর ওপর ভিত্তি করে)
                    try:
                        conn = sqlite3.connect('market_data.db')
                        df_dues = pd.read_sql_query("SELECT due FROM sales_ledger", conn)
                        conn.close()
                        total_stuck_cash = df_dues['due'].sum() if not df_dues.empty else 0
                        
                        if total_stuck_cash > 5000:
                            st.error(f"🚨 **Capital Liquidity Alert:** You have **৳{total_stuck_cash:,.2f}** stuck in market dues. AI strongly advises focusing on collection before importing or buying new accessory slots.")
                            alert_triggered = True
                    except:
                        pass
                        
                    if not alert_triggered:
                        st.success("🟢 **All Systems Optimal:** Your stock levels match current velocity and market dues are well within safe thresholds. No urgent actions needed.")
                else:
                    st.info("💡 Your trading ledger is fresh. Once you record sales or scan incoming wholesale memos, the AI Copilot will start flashing proactive restock alerts.")
            except Exception as e:
                st.error(f"Alert Engine Error: {e}")



    # ====================================================================
    # 6. RISK & MONEY MANAGEMENT (100% RESTORED INTERACTIVE SLIDERS)
    # ====================================================================
    elif menu == t['menu_risk']:
        st.subheader("🛡️ AI Capital Shield & Interactive Risk Simulator")
        st.markdown("Calculate safe inventory sizing, simulate market drops/hikes, and view your AI Risk Meter based on live wholesale data and market sentiment.")
        st.markdown("---")
        
        # 1. Fetch Unique Products for Dropdown
        scanned_products = []
        try:
            conn = sqlite3.connect('market_data.db')
            scanned_products = pd.read_sql_query("SELECT DISTINCT item FROM sales_ledger", conn)['item'].tolist()
            conn.close()
        except: pass
        
        if not scanned_products:
            # FALLBACK IF DB IS EMPTY
            scanned_products = ["AirPods Pro 2", "Lenovo LP40 TWS", "Apple Watch S9", "Smart Keyboard"]

        # 2. Top Interactive Section
        col1, col2 = st.columns(2)
        with col1:
            capital = st.number_input("Total Capital (BDT):", min_value=10000, value=100000, step=10000)
            selected_asset = st.selectbox("Target Import Asset:", scanned_products)
            
        # Get Latest Price (Mock logic for safety)
        latest_price = 1250 # Default baseline
        if selected_asset == "AirPods Pro 2": latest_price = 1250
        elif selected_asset == "Apple Watch S9": latest_price = 2400
        elif selected_asset == "Lenovo LP40 TWS": latest_price = 550
        
        if latest_price > 1000:
            sentiment = "Stable"
            safe_limit = 40
        else:
            sentiment = "High Demand"
            safe_limit = 70
            
        with col2:
            st.markdown(f"#### 📊 Market Pulse for {selected_asset}")
            if safe_limit >= 60:
                st.success(f"🔥 Sentiment: {sentiment} (Safe for Entry)")
            elif safe_limit >= 40:
                st.info(f"⚖️ Sentiment: {sentiment} (Proceed with Caution)")
            else:
                st.error(f"⚠️ Sentiment: Low Demand (High Risk of Dead Stock)")

        st.markdown("---")
        st.markdown("### ⚙️ Adjust Market Variables (Interactive Slider)")
        
                # --- এআই অটো-পাইলট লজিক (Risk Meter) ---
        try:
            conn = sqlite3.connect('market_data.db')
            # ডাটাবেস থেকে রিয়াল ডাটা আনা
            df_ledg = pd.read_sql_query("SELECT total_bill, due FROM sales_ledger", conn)
            conn.close()
            
            total_exposure = df_ledg['total_bill'].sum() if not df_ledg.empty else 100000
            total_due_amt = df_ledg['due'].sum() if not df_ledg.empty else 0
            # ডিউ রেশিও অনুযায়ী ডিফল্ট স্লাইডার পজিশন ঠিক করা
            current_due_ratio = (total_due_amt / total_exposure * 100) if total_exposure > 0 else 20
        except Exception:
            current_due_ratio = 20  # ডাটাবেস এরর হলে ২০% ডিফল্ট ধরা হবে
            total_due_amt = 0

        scol1, scol2, scol3 = st.columns(3)
        # স্লাইডারের ডিফল্ট ভ্যালু এখন ডায়নামিক এবং অটো-অ্যাডজাস্ট হবে
        with scol1:
            capital_usage_pct = st.slider("Capital Usage (%)", 10, 100, value=int(min(max(current_due_ratio + 10, 10), 100)))
        with scol2:
            markup_pct = st.slider("Expected Retail Margin (%)", 5, 100, value=25)
        with scol3:
            price_change_pct = st.slider("Simulate Market Price Spike/Drop (%)", -40, 40, value=0)

            
        # 3. Core Math Logic
        import_cost = latest_price
        expected_sell_price = import_cost * (1 + (markup_pct / 100))
        invested_amount = capital * (capital_usage_pct / 100)
        max_units = int(invested_amount // import_cost)
        actual_investment = max_units * import_cost
        
        simulated_sell_price = expected_sell_price * (1 + (price_change_pct / 100))
        simulated_profit_loss = (max_units * simulated_sell_price) - actual_investment
        
        st.markdown("#### 📊 Simulation Results")
        rcol1, rcol2, rcol3 = st.columns(3)
        rcol1.metric("Units You Can Buy", f"{max_units} pcs", f"Invest: ৳{int(actual_investment):,}", delta_color="off")
        rcol2.metric("Target Profit (Normal)", f"৳{int((max_units*expected_sell_price)-actual_investment):,}", f"Retail: ৳{int(expected_sell_price):,}", delta_color="off")
        
        delta_label = f"{price_change_pct}% Hike (Bullish)" if price_change_pct >= 0 else f"{abs(price_change_pct)}% Drop (Bearish)"
        rcol3.metric(delta_label, f"৳{int(simulated_profit_loss):,}", f"{price_change_pct}%", delta_color="normal" if price_change_pct >=0 else "inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        mcol1, mcol2 = st.columns([1, 1.2])
        
        # 4. GAUGE CHART (Dynamic based on slider)
        with mcol1:
            risk_score = capital_usage_pct + (abs(min(price_change_pct, 0)) * 1.2)
            risk_score = min(risk_score, 100)
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", value = risk_score,
                title = {'text': "AI Risk Meter", 'font': {'size': 16, 'color': 'white'}},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "rgba(0,0,0,0)"},
                    'bgcolor': "#1e1e1e",
                    'steps': [
                        {'range': [0, 40], 'color': "#00E676"},
                        {'range': [40, 75], 'color': "#FFC107"},
                        {'range': [75, 100], 'color': "#FF5252"}
                    ],
                    'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': risk_score}
                }
            ))
            fig.update_layout(height=210, margin=dict(t=50, b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
            st.plotly_chart(fig, use_container_width=True)

        with mcol2:
            st.markdown("#### 💰 Portfolio Allocation Breakdown")
            backup_capital = capital - actual_investment
            marketing_buffer = int(backup_capital * 0.15)
            emergency_cash = backup_capital - marketing_buffer
            
            st.success(f"📦 **Active Inventory ({capital_usage_pct}%):** ৳{int(actual_investment):,}")
            st.warning(f"📣 **Marketing & Ads Buffer:** ৳{marketing_buffer:,}")
            st.info(f"🛡️ **Emergency Cash Backup:** ৳{int(emergency_cash):,}")

        st.markdown("---")
        st.markdown("#### 🚨 Trade Wolf Guard Alerts")
        if risk_score > 75:
            st.error(f"**🔴 DANGER:** You are over-leveraged! A {abs(price_change_pct)}% market drop could wipe out your buffer. Reduce Capital Usage.")
        else:
            st.success(f"**🟢 SAFE:** Your allocation is optimized. The ৳{int(emergency_cash):,} backup protects you against sudden market volatility.")

    # ====================================================================
    # 7. IDEA VALIDATOR
    # ====================================================================
    elif menu == t['menu_validator']:
        st.subheader("🚀 Business Idea Validator (Free Beta)")
        st.markdown("Thinking of starting a new gadget business? Validate your market feasibility, calculate dropshipping vs retail risks, and get a realistic success score before investing a single taka.")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🎯 Target Market & Niche")
            location = st.selectbox("Target City/Region:", ["Dhaka", "Cumilla", "Chattogram", "Sylhet", "Rajshahi"])
            category = st.selectbox("Product Category:", ["TWS / Earbuds", "Smartwatches", "Premium Audio", "Mobile Accessories"])
            business_model = st.radio("Business Model:", ["Local Wholesale & Retail", "Dropshipping (Online)"])
        with col2:
            st.markdown("#### 💰 Financial Strategy")
            budget = st.number_input("Initial Investment Capital (BDT):", min_value=5000, value=20000, step=5000)
            target_margin = st.slider("Expected Profit Margin (%)", min_value=5, max_value=50, value=15)
            risk_tolerance = st.select_slider("Your Risk Tolerance:", options=["Low (Safe)", "Medium (Balanced)", "High (Aggressive)"])
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🧠 Generate Feasibility Report", use_container_width=True):
            with st.spinner(f"Analyzing {category} market heat in {location} and calculating competitive risks..."):
                GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 
                report = generate_idea_validation(location=location, category=category, business_model=business_model, budget=budget, margin=target_margin, risk=risk_tolerance, api_key=GEMINI_API_KEY)
                st.success("✅ Custom Market Analysis Complete!")
                st.markdown(report)
                st.markdown("---")
                st.markdown("<h4 style='text-align: center; color: #FFC107;'>Want the live WhatsApp supplier list and real-time margin tracking for this specific idea?</h4>", unsafe_allow_html=True)
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1.5, 1])
                with col_btn2:
                    st.button("🔒 Unlock Premium Dashboard", use_container_width=True, type="primary")
    
    # ====================================================================
    # 8. RAG (DOCUMENT AI)
    # ====================================================================
    elif menu == t['menu_rag']:
        st.subheader("📄 AI Report Analysis (RAG)")
        st.markdown("Upload any Market Survey (PDF) or Sales Report (CSV) and chat directly with your data.")
        with st.expander("📁 Document Upload & Configuration", expanded=True):
            up_col1, up_col2 = st.columns([2, 1])
            with up_col1:
                uploaded_file = st.file_uploader("Upload your PDF or CSV file here", type=['pdf', 'csv'])
            with up_col2:
                ai_model = st.radio("Select AI Engine:", ["Groq (Fast & Free)", "Gemini"])
                process_btn = st.button("🚀 Process Document", use_container_width=True)
            if process_btn:
                if uploaded_file:
                    with st.spinner("Processing & building Vector Database..."):
                        raw_text = extract_text_from_file(uploaded_file)
                        vector_store = build_vector_database(raw_text)
                        st.session_state["vector_store"] = vector_store
                        st.session_state["chat_history"] = []
                        st.success("✅ Document processed! You can now chat below.")
                else:
                    st.warning("⚠️ Please upload a file first.")
        st.markdown("---")
        st.markdown("### 💬 Chat with your Data")
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
        for message in st.session_state["chat_history"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        if query := st.chat_input("Ask a question about the report..."):
            if "vector_store" in st.session_state:
                st.session_state["chat_history"].append({"role": "user", "content": query})
                with st.chat_message("user"):
                    st.markdown(query)
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing document context..."):
                        model_choice = "groq" if "Groq" in ai_model else "gemini"
                        response = analyze_report_with_ai(query, st.session_state["vector_store"], model_choice)
                        st.markdown(response)
                        st.session_state["chat_history"].append({"role": "assistant", "content": response})
            else:
                st.error("⚠️ Please process a document first from the section above.")

    
    # ==========================================
    # 9. ORDER INBOX 📥 (WHATSAPP SALES LEDGER)
    # ==========================================
    elif menu == t['menu_ledger']:
        st.subheader(t['sales_title'])
        st.caption(t['sales_cap'])
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1.5])
        
        # 🎙️ বামদিকের প্যানেল: Order Inbox (ভয়েস এবং টেক্সট)
        with col1:
            st.markdown(f"### 📥 Order Inbox")
            st.info(f"💡 **উদাহরণ:** {t['sales_info']}")
            
            tab_voice, tab_text = st.tabs(["🎙️ Voice Order", "💬 Text Order"])
            
            # --- TAB 1: VOICE ORDER (Order Inbox) ---
            with tab_voice:
                # ১. ফাইল আপলোড অপশন
                sale_audio_file = st.file_uploader("Upload WhatsApp Voice Note File", type=["mp3", "wav", "m4a"], key="ledger_file_uploader")
                
                # ২. সরাসরি রেকর্ড করার অপশন
                from streamlit_mic_recorder import mic_recorder
                audio_record = mic_recorder(start_prompt="🎤 Click to Record Live Voice", stop_prompt="🛑 Stop Recording", key="ledger_live_voice")
                
                audio_bytes = None
                if sale_audio_file is not None:
                    audio_bytes = sale_audio_file.getvalue()
                elif audio_record is not None:
                    # mic_recorder returns a dictionary, we extract 'bytes'
                    audio_bytes = audio_record['bytes'] 
                
                if audio_bytes is not None:
                    if st.button("🧠 Extract Voice Details", type="primary", use_container_width=True, key="btn_extract_voice"):
                        with st.spinner("AI ইভ্যালুয়েট করছে..."):
                            
                            GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
                            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
                            prompt = f'''Extract details from: "{sale_audio_file}". Return JSON: {{"customer_name": "...", "item_name": "...", "quantity": X, "unit_price": X, "paid_amount": X}}.'''
                            payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}}
                            
                            api_success = False
                        with st.spinner("AI মেসেজ রিড করছে..."):
                            try:
                                payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}}
                                response = requests.post(url, json=payload).json()
                                
                                if 'error' in response:
                                    raise Exception(response['error']['message'])
                                    
                                ai_json = response['candidates'][0]['content']['parts'][0]['text']
                                st.session_state['temp_order'] = json.loads(ai_json)
                                st.session_state['order_source'] = 'ledger'
                                api_success = True
                                
                            except Exception as e:
                                # 🚨 API ফেইল করলে রেড এরর না দিয়ে সাইলেন্টলি ফলব্যাক ট্রিগার করবে
                                api_success = False
                        
                        if not api_success:
                            st.warning("⚠️ সার্ভার অতিরিক্ত ব্যস্ত থাকায় AI সাময়িকভাবে কাজ করছে না। আপনার সময় বাঁচাতে ম্যানুয়াল এন্ট্রি প্যানেল চালু করা হলো।")
                            # AI ফেইল করলে ইউজারের ইনপুট করা টেক্সট থেকেই ম্যানুয়ালি ডাটা বসানোর সুযোগ করে দেওয়া হলো
                            st.session_state['temp_order'] = {
                                "customer_name": "New Customer", 
                                "item_name": "Item", 
                                "quantity": 1, 
                                "unit_price": 0.0, 
                                "paid_amount": 0.0
                            }
                            st.session_state['order_source'] = 'ledger'


            # --- TAB 2: TEXT ORDER ---
            with tab_text:
                whatsapp_text = st.chat_input("Paste customer text here (e.g. 5 AirPods 600tk)")
                if whatsapp_text and st.button("🧠 Extract Text Details", type="primary", use_container_width=True, key="btn_extract_text"):
                    with st.spinner("AI মেসেজ রিড করছে..."):
                        import requests, json
                        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
                        prompt = f'''Extract details from: "{whatsapp_text}". Return JSON: {{"customer_name": "...", "item_name": "...", "quantity": X, "unit_price": X, "paid_amount": X}}.'''
                        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}}
                        
                        api_success = False
                    with st.spinner("AI মেসেজ রিড করছে..."):
                        try:
                            payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}}
                            response = requests.post(url, json=payload).json()
                            
                            if 'error' in response:
                                raise Exception(response['error']['message'])
                                
                            ai_json = response['candidates'][0]['content']['parts'][0]['text']
                            st.session_state['temp_order'] = json.loads(ai_json)
                            st.session_state['order_source'] = 'ledger'
                            api_success = True
                            
                        except Exception as e:
                            # 🚨 API ফেইল করলে রেড এরর না দিয়ে সাইলেন্টলি ফলব্যাক ট্রিগার করবে
                            api_success = False
                    
                    if not api_success:
                        st.warning("⚠️ সার্ভার অতিরিক্ত ব্যস্ত থাকায় AI সাময়িকভাবে কাজ করছে না। আপনার সময় বাঁচাতে ম্যানুয়াল এন্ট্রি প্যানেল চালু করা হলো।")
                        # AI ফেইল করলে ইউজারের ইনপুট করা টেক্সট থেকেই ম্যানুয়ালি ডাটা বসানোর সুযোগ করে দেওয়া হলো
                        st.session_state['temp_order'] = {
                            "customer_name": "New Customer", 
                            "item_name": "Item", 
                            "quantity": 1, 
                            "unit_price": 0.0, 
                            "paid_amount": 0.0
                        }
                        st.session_state['order_source'] = 'ledger'

                        
            # --- 🛡️ UX সেভিয়ার: ডাটাবেসে সেভ করার আগে রিভিও এবং এডিট ফর্ম প্যানেল ---
            if 'temp_order' in st.session_state and st.session_state.get('order_source') == 'ledger':
                st.markdown("---")
                st.markdown("### 📝 Review & Edit Extracted Order")
                st.caption("ভুল এড়াতে ডাটাবেসে এন্ট্রি হওয়ার আগে নিচে কাস্টমাইজ বা কারেকশন করে নিন।")
                
                order_data = st.session_state['temp_order']
                
                # ইনপুট ফিল্ড যা ইউজারকে এডিট করার ফুল এক্সেস দেয়
                edit_cust = st.text_input("Customer Name:", value=order_data.get("customer_name", "Unknown"))
                edit_item = st.text_input("Item Name:", value=order_data.get("item_name", "Item"))
                edit_qty = st.number_input("Quantity:", min_value=1, value=int(order_data.get("quantity", 1)))
                edit_price = st.number_input("Unit Price (৳):", min_value=0.0, value=float(order_data.get("unit_price", 0)))
                edit_paid = st.number_input("Cash Paid (৳):", min_value=0.0, value=float(order_data.get("paid_amount", 0)))
                
                t_bill = edit_qty * edit_price
                t_due = max(0.0, t_bill - edit_paid)
                
                st.info(f"📊 **লাইভ হিসাব:** মোট বিল: ৳{t_bill:,.0f} | বাকি ডিউ: ৳{t_due:,.0f}")
                
                cb1, cb2 = st.columns(2)
                with cb1:
                    if st.button("💾 Confirm & Save to Ledger", type="primary", use_container_width=True):
                        conn = sqlite3.connect('market_data.db')
                        c = conn.cursor()
                        c.execute("INSERT INTO sales_ledger (customer, item, qty, unit_price, total_bill, paid, due) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                  (edit_cust, edit_item, edit_qty, edit_price, t_bill, edit_paid, t_due))
                        conn.commit()
                        conn.close()
                        # 📄 Smart Invoice ডাটা সেশনে সেভ করা হলো যেন রিলোডে মুছে না যায়
                        st.session_state['invoice_data'] = f"🐺 TRADE WOLF RECEIPT\n-----------------------\nCustomer: {edit_cust}\nItem: {edit_item} (x{edit_qty})\n-----------------------\nTotal Bill: ৳{t_bill:,.0f}\nPaid: ৳{edit_paid:,.0f}\nDue: ৳{t_due:,.0f}\n-----------------------\nPowered by Trade Wolf AI"
                        
                        del st.session_state['temp_order']
                        del st.session_state['order_source']
                        st.rerun()
                with cb2:
                    if st.button("🗑️ Cancel / Discard Data", use_container_width=True):
                        del st.session_state['temp_order']
                        del st.session_state['order_source']
                        st.warning("❌ ডেটা বাতিল করা হয়েছে।")
                        st.rerun()

            # --- 📄 স্মার্ট ইনভয়েস ডিসপ্লে প্যানেল ---
            if 'invoice_data' in st.session_state:
                st.markdown("---")
                st.success("✅ নিখুঁতভাবে লেজারে এন্ট্রি সেভ করা হয়েছে!")
                st.markdown("### 📄 Generated Smart Invoice")
                st.code(st.session_state['invoice_data'])
                st.download_button("📥 Download Invoice", st.session_state['invoice_data'], file_name="TradeWolf_Invoice.txt", use_container_width=True)
                if st.button("✖️ Close Invoice", use_container_width=True):
                    del st.session_state['invoice_data']
                    st.rerun()

            # --- 🚀 SMART INVOICE GENERATOR (For BOTH Voice and Text) ---
            if 'last_order' in st.session_state:
                o = st.session_state['last_order']
                st.markdown("---")
                memo_txt = f"""
🐺 TRADE WOLF SMART RECEIPT 🐺
-------------------------------
Customer: {o['customer']}
Date: {time.strftime('%Y-%m-%d')}
-------------------------------
Item: {o['item']}
Qty: {o['qty']} @ ৳{o['price']:,.0f}
-------------------------------
Total Bill: ৳{o['total']:,.0f}
Cash Paid: ৳{o['paid']:,.0f}
DUE AMOUNT: ৳{o['due']:,.0f}
-------------------------------
Generated by: Trade Wolf AI
"""
                st.code(memo_txt, language="markdown")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.download_button(label="📥 Download Receipt", data=memo_txt, file_name=f"Memo_{o['customer']}.txt", mime="text/plain", use_container_width=True)
                with col_btn2:
                    if st.button("🔄 Clear & New Order", use_container_width=True):
                        del st.session_state['last_order']
                        st.rerun()

       # --- ডানদিকের প্যানেল: এরর-ফ্রি ডিউ খাতা ফিক্স ---
        with col2:
            st.markdown(f"### {t['sales_ledger']}")
            try:
                conn = sqlite3.connect('market_data.db')
                # Strict কলামের ঝামেলা এড়াতে * দিয়ে ডাটা টানা হলো
                df = pd.read_sql_query("SELECT * FROM sales_ledger", conn)
                conn.close()
                
                if not df.empty:
                    # ডাটাবেসের আবর্জনা সাফ করা
                    df = df.dropna(subset=['customer', 'item'])
                    df = df[df['customer'].astype(str) != 'None']
                    df = df[df['customer'].astype(str) != 'nan']
                    
                    # মেট্রিক্স হিসাব (ক্যাপিটাল লেটার বা স্মল লেটার যাই হোক, সেফ হ্যান্ডলিং)
                    due_col = 'due' if 'due' in df.columns else 'Due'
                    paid_col = 'paid' if 'paid' in df.columns else 'Paid'
                    
                    m1, m2 = st.columns(2)
                    m1.metric("Total Dues", f"৳{df[due_col].sum():,.2f}")
                    m2.metric("Cash Collected", f"৳{df[paid_col].sum():,.2f}")
                    
                    # ডিসপ্লে করার জন্য কলাম রি-ম্যাপ
                    disp_df = pd.DataFrame()
                    disp_df['Customer'] = df['customer'] if 'customer' in df.columns else df['Customer']
                    disp_df['Item'] = df['item'] if 'item' in df.columns else df['Item']
                    disp_df['Qty'] = df['qty'] if 'qty' in df.columns else df['Qty']
                    disp_df['Paid'] = df[paid_col]
                    disp_df['Due'] = df[due_col]
                    
                    st.dataframe(disp_df, hide_index=True, use_container_width=True)
                    
                    # --- AI Due Recovery ---

                    st.markdown("---")
                    st.markdown("#### 🔔 AI Due Recovery")
                    due_custs = disp_df[disp_df['Due'] > 0]['Customer'].unique().tolist()
                    if due_custs:
                        target = st.selectbox("Select Customer to Remind:", due_custs)
                        if st.button("✨ Draft Reminder", use_container_width=True):
                            # ডাইনামিক মেসেজ তৈরি
                            customer_due = df[df['customer'] == target]['due'].iloc[0]
                            st.session_state['drafted_msg'] = f"Assalamu Alaikum {target}, apnar ৳{customer_due:,.0f} due baki ache. Ektu taratari clear korle upokar hoto. Dhonnobad!"
                        
                        if 'drafted_msg' in st.session_state:
                            st.info(st.session_state['drafted_msg'])
                            import urllib.parse
                            encoded_msg = urllib.parse.quote(st.session_state['drafted_msg'])
                            link = f"https://wa.me/?text={encoded_msg}"
                            st.markdown(f'<a href="{link}" target="_blank" style="background:#25D366;color:white;padding:12px;display:block;text-align:center;text-decoration:none;border-radius:8px;font-weight:bold;">📲 Send via WhatsApp</a>', unsafe_allow_html=True)
                    else:
                        st.success("🎉 All clear! No pending dues to collect.")
                else:
                    st.info("No orders recorded yet. Start processing orders from the left panel!")
            except Exception as e:
                st.error(f"Database sync error: {e}")