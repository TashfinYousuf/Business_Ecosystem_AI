import io
import base64
import os
import requests
import json
from google import genai
from groq import Groq
from PIL import Image


# ১. API Keys Setup
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

def get_market_insight(product_name, current_price, usd_rate, preferred_model="groq"):
    """
    Multi-model logic: You can switch between 'gemini' and 'groq' (Llama 3).
    Groq is extremely fast and free, good for instant reasoning.
    """
    
    prompt = f"""
    You are a highly analytical Bangladeshi Market Expert. 
    Product: {product_name}
    Current Market Price: ৳{current_price}
    Current USD to BDT Rate: ৳{usd_rate}
    
    Provide a direct, strictly 3-bullet-point insight on:
    1. Demand prediction logic
    2. Import/Investment risk
    3. Suggested business action
    Keep it extremely concise and professional.
    """
    
    try:
        if preferred_model == "groq":
            # Groq (Llama 3.1) - Updated Fast & Free Alternative
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant", # মডেলের নাম আপডেট করা হলো
                temperature=0.1,
            )
            return chat_completion.choices[0].message.content
            
        elif preferred_model == "gemini":
            # Gemini 2.5 Flash
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text
            
    except Exception as e:
        return f"AI Analysis Failed ({preferred_model}): {e}"

# Testing the Multi-Model
if __name__ == "__main__":
    print("Testing Groq (Llama 3.1)...")
    print(get_market_insight("MacBook Air M5", 150000, 118.50, preferred_model="groq"))


def generate_idea_validation(location, category, business_model, budget, margin, risk, api_key):
    from google import genai
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are a highly practical SME Business Consultant and Market Expert in Bangladesh.
    Evaluate the feasibility of the following business idea:
    - Target City/Region: {location}
    - Product Category: {category}
    - Business Model: {business_model}
    - Initial Budget: {budget} BDT
    - Expected Profit Margin: {margin}%
    - Risk Tolerance: {risk}

    Provide a realistic, data-driven analysis. Output STRICTLY in the following Markdown format. Do not add conversational filler text.

    ### 📊 Market Feasibility Score: [Score out of 100] ([Verdict: Highly Favorable / Moderate / Risky])

    #### ✅ Key Strengths & Opportunities:
    - [Provide 2-3 specific bullet points tailored exactly to {location} and {category}]
    - [Mention if the budget of {budget} BDT is sufficient for this model]

    #### ⚠️ Potential Risks & Reality Check:
    - [Provide 2-3 specific risks regarding competition, {margin}% profit margin viability, or supply chain]
    - [Mention local challenges in {location}]
    """
    
    try:
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return res.text
    except Exception as e:
        return f"⚠️ AI Analysis Failed. Please check your API Key or Connection. Error: {e}"
    


def extract_data_from_memo(image_bytes, api_key):
    # ১. Direct REST API URL for Gemini
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # ২. Convert raw bytes to Base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    prompt = """
    You are an expert Data Extraction AI for Bangladesh Wholesale Markets.
    Analyze this handwritten or printed memo/invoice.
    Extract the billing data STRICTLY as a JSON object with the following structure:
    {
      "customer_name": "Name of the client/shop on the memo (default 'Unknown')",
      "items": [
        {"product_name": "Name", "quantity": 1, "unit_price": 100, "total_price": 100}
      ],
      "total_bill": 100,
      "paid_amount": 100,
      "due_amount": 0
    }
    
    If the memo shows a discount, subtract it from total_bill.
    CRITICAL: Output ONLY the raw JSON object. Do NOT wrap in ```json ``` blocks.
    """
    
    # Payload-এ response_mime_type "application/json" অ্যাড করে দিলে গুগল বাধ্য হবে JSON দিতে
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": base64_image
                    }
                }
            ]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"  # The Game Changer
        }
    }
    
    # ৩. [FIXED] API strict CamelCase format (inlineData, mimeType)
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inlineData": {  # ঠিক করা হয়েছে
                        "mimeType": "image/jpeg",  # ঠিক করা হয়েছে
                        "data": base64_image
                    }
                }
            ]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        json_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        response = requests.post(url, headers=headers, data=json_data)
        
        # যদি 400 বা অন্য কোনো এরর আসে, তাহলে গুগলের আসল মেসেজটা প্রিন্ট করবে
        if response.status_code != 200:
            return f"⚠️ API Error ({response.status_code}): {response.text}"
            
        result = response.json()
        extracted_text = result['candidates'][0]['content']['parts'][0]['text']
        return extracted_text
        
    except Exception as e:
        return f"⚠️ Server Connection Failed: {e}"
    

def generate_product_insight(product_name, history_data, api_key):
    from google import genai
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are 'Trade Wolf', an elite AI Business Copilot and Guardian Angel for the Bangladeshi SME and E-commerce market.
    Analyze the following real-time wholesale pricing history for the product: '{product_name}'.
    
    Pricing History Data (Date, Price, Status):
    {history_data}

    Provide a short, highly actionable, and data-driven market intelligence report in Markdown format.
    Your analysis MUST be divided into two specific perspectives:
    
    #### 📦 For Current Stock Holders (Importers/Wholesalers):
    - Should they hold, liquidate (discount), or push sales? 
    - Are there any 'Dead Stock' risks based on the price trend?

    #### 🚀 For New Entrepreneurs (SMEs/Youth):
    - Is this a safe product to invest capital in right now? 
    - What are the entry risks, scam warnings, and profit potentials based on these wholesale rates?

    Keep the tone professional, urgent, and highly practical. Give realistic advice suitable for the BD market context.
    """
    
    try:
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return res.text
    except Exception as e:
        return f"⚠️ AI Insight Generation Failed. Error: {e}"
    

def generate_math_prediction(product_name, wholesale_price, retail_price, api_key):
    from google import genai
    client = genai.Client(api_key=api_key)
    
    # Mathematical Prompt for AI
    prompt = f"""
    You are 'Trade Wolf Quant', an elite algorithmic trading AI for the Bangladesh E-commerce market.
    Analyze the following REAL-TIME arbitrage data:
    
    - Target Asset: {product_name}
    - Current Wholesale Cost: ৳{wholesale_price}
    - Live Retail Market Price: ৳{retail_price}
    
    Calculate and output ONLY the following structured format (use exact math):
    
    **Gross Margin:** [Calculate % margin]
    **Net Profit Estimate:** [Assume 5% marketing cost and 2% delivery return loss, show final BDT profit]
    **Risk Index:** [Low/Medium/High based on margin width]
    **AI Verdict:** [1 sentence actionable decision: e.g., "Aggressive Buy. Margin is wide enough to absorb market shocks."]
    """
    
    try:
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return res.text
    except Exception as e:
        return f"⚠️ Prediction Failed: {e}"
    


def extract_sales_from_audio(audio_bytes, mime_type, api_key):
    """
    Listens to voice notes and extracts ONLY RAW DATA. Math is handled by Python later.
    """
    base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = """
    You are a highly accurate Bengali/Banglish Audio Transcription AI for wholesale businesses.
    Listen to the audio carefully. Extract the exact names and numbers mentioned. 
    
    CRITICAL RULES:
    1. NEVER output examples from your memory. ONLY output what is exactly spoken in the audio.
    2. Extract these 4 things: Customer Name, Item Name, Quantity, and Unit Price (or Paid Amount).
    3. If quantity is not explicitly mentioned, assume it is 1.
    4. If the paid amount is not mentioned, assume 0.
    5. DO NOT do any math (like calculating total bills). Just extract the raw numbers spoken.
    
    Output strictly in this JSON format:
    {
        "customer_name": "Tuhin Bhai",
        "item_name": "AirPods Pro",
        "quantity": 2,
        "unit_price": 600,
        "paid_amount": 1000
    }
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": mime_type, "data": base64_audio}}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        raise Exception(f"AI Audio Extraction Failed: {str(e)}")