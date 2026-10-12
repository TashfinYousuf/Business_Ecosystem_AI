import sqlite3
import pandas as pd
import bcrypt
from datetime import datetime, timedelta

DB_NAME = "market_data.db"


def init_db():
    conn = sqlite3.connect('market_data.db')
    c = conn.cursor()
    
    # আগের স্ক্যানার টেবিল
    c.execute('''CREATE TABLE IF NOT EXISTS memo_tracker
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_name TEXT, price REAL, status TEXT, 
                  scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                  
    # 🆕 নতুন টেবিল: WhatsApp Sales Ledger এর জন্য
    c.execute('''CREATE TABLE IF NOT EXISTS sales_ledger
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  customer TEXT, item TEXT, qty INTEGER, 
                  unit_price REAL, total_bill REAL, paid REAL, due REAL, 
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                  
    conn.commit()
    conn.close()

# 🆕 নতুন ডাটা সেভ করার ফাংশন
def insert_sale_data(customer, item, qty, unit_price, total_bill, paid, due):
    conn = sqlite3.connect('market_data.db')
    c = conn.cursor()
    c.execute('''INSERT INTO sales_ledger 
                 (customer, item, qty, unit_price, total_bill, paid, due) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (customer, item, qty, unit_price, total_bill, paid, due))
    conn.commit()
    conn.close()


# --- Price Data Functions ---
def insert_price_data(product_name, price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT id FROM price_history WHERE date=? AND product_name=?", (today_date, product_name))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute('INSERT INTO price_history (date, product_name, price) VALUES (?, ?, ?)', (today_date, product_name, price))
        conn.commit()
    conn.close()

def get_price_history(product_name):
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT date, price FROM price_history WHERE product_name = '{product_name}' ORDER BY date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# --- Secure Authentication Functions ---
def register_user(username, email, phone, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Hash the password securely
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        cursor.execute('''
            INSERT INTO users (username, email, phone, password_hash, is_verified)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, phone, hashed.decode('utf-8'), 0)) # 0 means not verified yet
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False # Email already exists

def verify_and_login_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # Check password hash
        if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            return {"status": "success", "username": user[1]}
    return {"status": "failed"}

def verify_account(email):
    # Dummy verification function
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_verified = 1 WHERE email=?", (email,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()


def insert_memo_data(product_name, price, status):
    conn = sqlite3.connect('market_data.db')
    c = conn.cursor()
    
    # টেবিল না থাকলে তৈরি করে নিবে (Product Name, Price, Status, Date)
    c.execute('''CREATE TABLE IF NOT EXISTS memo_tracker
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_name TEXT,
                  price REAL,
                  status TEXT,
                  scan_date TEXT)''')
    
    # ডাটা ইনসার্ট করা
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO memo_tracker (product_name, price, status, scan_date) VALUES (?, ?, ?, ?)",
              (product_name, price, status, current_date))
    
    conn.commit()
    conn.close()


def get_scanned_products():
    try:
        conn = sqlite3.connect('market_data.db')
        c = conn.cursor()
        # শুধু ইউনিক প্রোডাক্টের নামগুলো আনবে
        c.execute("SELECT DISTINCT product_name FROM memo_tracker WHERE product_name != 'Unknown'")
        products = [row[0] for row in c.fetchall()]
        conn.close()
        return products
    except Exception as e:
        return []

def get_product_history(product_name):
    try:
        conn = sqlite3.connect('market_data.db')
        # নির্দিষ্ট প্রোডাক্টের তারিখ অনুযায়ী দাম আনবে
        query = "SELECT scan_date, price, status FROM memo_tracker WHERE product_name = ? ORDER BY scan_date ASC"
        df = pd.read_sql_query(query, conn, params=(product_name,))
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()
    

def get_live_terminal_data():
    
    try:
        conn = sqlite3.connect('market_data.db')
        # কোন প্রোডাক্ট কতবার স্ক্যান হয়েছে (entry_count) এবং তার গড় দাম কত, সেটা বের করবে
        query = """
        SELECT product_name, COUNT(id) as entry_count, AVG(price) as avg_price 
        FROM memo_tracker 
        WHERE product_name != 'Unknown' 
        GROUP BY product_name 
        ORDER BY entry_count DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()

def get_trust_scores():
   
    try:
        conn = sqlite3.connect('market_data.db')
        # একই প্রোডাক্টের কতগুলো ভিন্ন ভিন্ন দাম (price_variants) বাজারে চলছে, সেটা বের করবে
        query = """
        SELECT product_name, COUNT(DISTINCT price) as price_variants 
        FROM memo_tracker 
        WHERE product_name != 'Unknown' AND price > 0
        GROUP BY product_name 
        ORDER BY price_variants DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()
    

def get_market_sentiment(product_name):
    """
    Returns AI-driven market sentiment based on product categories and scan trends.
    """
    name_lower = str(product_name).lower()
    
    # Simple logic mapping for the demonstration
    if any(keyword in name_lower for keyword in ["pro", "tws", "magsafe", "watch 9", "ultra"]):
        return "High Demand (Trending)"
    elif any(keyword in name_lower for keyword in ["wired", "budget", "standard", "silicone"]):
        return "Saturated (High Risk)"
    else:
        return "Stable"
    

def get_live_inventory():
    import pandas as pd
    import sqlite3
    try:
        conn = sqlite3.connect('market_data.db')
        # শুধু লেটেস্ট স্ক্যান করা ডাটা (MAX id) নিয়ে আসার স্মার্ট SQL কোয়েরি
        query = """
        SELECT product_name, price, status, scan_date 
        FROM memo_tracker 
        WHERE id IN (
            SELECT MAX(id) 
            FROM memo_tracker 
            GROUP BY product_name
        )
        ORDER BY scan_date DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()
    

def init_db():
    conn = sqlite3.connect('market_data.db')
    c = conn.cursor()
    # আগের memo_tracker টেবিল যদি থাকে, সেটা এভাবেই থাকবে
    c.execute('''CREATE TABLE IF NOT EXISTS memo_tracker
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, price REAL, status TEXT, scan_date TEXT)''')
                 
    # 🆕 নতুন: কাস্টমারদের হিসাব রাখার পার্মানেন্ট সেলস টেবিল
    c.execute('''CREATE TABLE IF NOT EXISTS sales_ledger
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, item TEXT, qty INTEGER, unit_price REAL, total_bill REAL, paid REAL, due REAL, sale_date TEXT)''')
    conn.commit()
    conn.close()

def record_new_sale(customer, item, qty, unit_price, total_bill, paid, due):
    """ভয়েস থেকে পাওয়া ১০০% নির্ভুল ডাটা এখানে পার্মানেন্ট সেভ হবে"""
    conn = sqlite3.connect('market_data.db')
    c = conn.cursor()
    sale_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute('''INSERT INTO sales_ledger (customer, item, qty, unit_price, total_bill, paid, due, sale_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
              (customer, item, qty, unit_price, total_bill, paid, due, sale_date))
    conn.commit()
    conn.close()

def get_all_sales():
    """সব সেলস ডাটা টেনে আনার ফাংশন"""
    conn = sqlite3.connect('market_data.db')
    df = pd.read_sql_query("SELECT customer as Customer, item as Item, qty as Qty, unit_price as 'Unit Price', total_bill as 'Total Bill', paid as Paid, due as Due, sale_date as Date FROM sales_ledger ORDER BY sale_date DESC", conn)
    conn.close()
    return df

def clean_garbage_data():
    conn = sqlite3.connect('market_data.db')
    c = conn.cursor()
    # নাম বা আইটেম ফাঁকা থাকলে সেই রো ডিলিট করে দিবে
    c.execute("DELETE FROM sales_ledger WHERE customer IS NULL OR item IS NULL OR customer = 'None' OR customer = 'nan'")
    conn.commit()
    conn.close()