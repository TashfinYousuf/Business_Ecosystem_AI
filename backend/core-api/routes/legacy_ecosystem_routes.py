"""
backend/core-api/routes/legacy_ecosystem_routes.py
FastAPI Router exposing all legacy Streamlit MVP features and functions:
- Authentication (Login, Register, 4-digit OTP Verification '1234') & Bilingual UI Dictionary (EN/BN)
- Live Market Terminal (Gainers, Losers, 7-Day Pulse, Live StarTech Scraper & AI Quant Arbitrage)
- Macro & Micro Market Overview (National Pulse, Live USD/BDT, Gold/Oil/S&P500, Private Asset Wallet)
- Supplier Trust Radar (SME Guardian Crowdsourced Memo Price Consistency & Scam Alerts)
- AI Product & Trend Analytics (Personal Ledger Analytics, Community Price Benchmark, Proactive AI Alerts Flywheel)
- AI Capital Shield & Interactive Risk Simulator (Dynamic Sliders, Risk Gauge, Portfolio Allocation, Guard Alerts)
- Business Idea Validator (SME Market Feasibility Report Generator)
- Smart Memo Scanner & Wholesale Inventory Commit (Image Memo, Voice Purchase, Text Purchase, Batch Stock Editor)
- WhatsApp Order Inbox & Customer Dues Ledger (Voice/Text Order Extraction, Edit & Confirm, Smart Receipt, AI Due Recovery & wa.me Link)
- Document Chat AI / RAG (PDF/CSV Upload, Vector Store Indexing, Groq/Gemini Corporate Analyst Chat)
"""

from __future__ import annotations

import base64
import time
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
from fastapi import APIRouter, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from domain.legacy_ai_services import (
    ENTERPRISE_UI_TEXT,
    analyze_report_with_ai,
    build_rag_index,
    extract_data_from_memo,
    extract_purchase_or_order_from_text,
    extract_sales_from_audio,
    extract_text_from_file_bytes,
    generate_idea_validation,
    generate_math_prediction,
    generate_product_insight,
    get_flywheel_analytics,
    get_market_insight,
    get_risk_simulator_context,
    simulate_capital_risk,
)
from domain.legacy_store import (
    commit_inventory_items,
    get_all_sales,
    get_live_inventory,
    get_price_history,
    get_product_history,
    get_scanned_products,
    get_wallet_inventory,
    insert_memo_data,
    insert_price_data,
    record_new_sale,
    register_user,
    verify_account,
    verify_and_login_user,
)
from domain.market_data_engine import (
    get_global_indicators,
    get_live_market_terminal_snapshot,
    get_live_product_price,
    get_live_usd_rate,
    get_national_market_pulse,
    get_supplier_trust_radar,
    scrape_real_retail_data,
)
from middleware.auth_middleware import JWT_ALGORITHM, JWT_SECRET_KEY

router = APIRouter(prefix="/api/v1", tags=["Legacy Streamlit Ecosystem"])

DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"


def _issue_jwt_for_user(user_id: str, username: str, org_id: str = DEFAULT_ORG_ID) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "org_id": org_id,
        "role": "OWNER",
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# =====================================================================
# PYDANTIC REQUEST SCHEMAS
# =====================================================================
class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthRegisterRequest(BaseModel):
    full_name: str
    email: str
    phone: str = ""
    password: str


class AuthVerifyOTPRequest(BaseModel):
    email: str
    otp: str = Field(description="4-digit OTP (use '1234' for testing)")


class ArbitrageScanRequest(BaseModel):
    category: str = "smart-watch"
    assumed_wholesale_discount: float = 0.65
    attempt_network: bool = False


class LiveProductPriceRequest(BaseModel):
    url: str


class MarketInsightRequest(BaseModel):
    product_name: str
    current_price: float
    usd_rate: float = 118.50
    preferred_model: str = "groq"


class ProductInsightRequest(BaseModel):
    product_name: str


class RiskSimulationRequest(BaseModel):
    capital: float = 100000.0
    selected_asset: str = "AirPods Pro 2"
    capital_usage_pct: int = 30
    markup_pct: int = 25
    price_change_pct: int = 0


class IdeaValidationRequest(BaseModel):
    location: str = "Dhaka"
    category: str = "TWS / Earbuds"
    business_model: str = "Local Wholesale & Retail"
    budget: float = 20000.0
    margin: int = 15
    risk: str = "Medium (Balanced)"


class ImageMemoExtractRequest(BaseModel):
    image_base64: Optional[str] = None
    mime_type: str = "image/jpeg"


class VoiceExtractRequest(BaseModel):
    audio_base64: Optional[str] = None
    mime_type: str = "audio/wav"
    transcript_hint: Optional[str] = None


class TextExtractRequest(BaseModel):
    text: str


class InventoryCommitItem(BaseModel):
    product_name: str
    unit_price: float = Field(ge=0)
    quantity: int = Field(ge=1, default=1)


class InventoryCommitRequest(BaseModel):
    items: List[InventoryCommitItem]


class ConfirmOrderRequest(BaseModel):
    customer_name: str
    item_name: str
    quantity: int = Field(ge=1, default=1)
    unit_price: float = Field(ge=0.0, default=0.0)
    paid_amount: float = Field(ge=0.0, default=0.0)


class DraftReminderRequest(BaseModel):
    customer_name: str


class RAGProcessDocumentRequest(BaseModel):
    filename: str
    file_base64: Optional[str] = None
    raw_text: Optional[str] = None


class RAGChatRequest(BaseModel):
    query: str
    model_choice: str = "groq"


# =====================================================================
# 0. AUTHENTICATION, OTP & BILINGUAL UI DICTIONARY
# =====================================================================
@router.get("/ui/dictionary")
async def get_ui_dictionary():
    """Returns the bilingual (EN / BN) Enterprise UI/UX dictionary from app.py."""
    return ENTERPRISE_UI_TEXT


@router.post("/auth/login")
async def login_merchant_user(payload: AuthLoginRequest):
    """Verifies merchant credentials against market_data.db and returns a JWT token."""
    res = verify_and_login_user(payload.email, payload.password)
    if res.get("status") == "success":
        token = _issue_jwt_for_user(res["user_id"], res["username"])
        return {
            "status": "success",
            "logged_in": True,
            "username": res["username"],
            "email": res["email"],
            "access_token": token,
            "org_id": DEFAULT_ORG_ID,
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials. Please try again.",
    )


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register_merchant_user(payload: AuthRegisterRequest):
    """Registers a new merchant account and triggers the 4-digit OTP verification flow."""
    if not payload.full_name or not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="Please fill all required fields.")

    ok = register_user(payload.full_name, payload.email, payload.phone, payload.password)
    if not ok:
        raise HTTPException(status_code=409, detail="Email already registered. Try logging in.")

    return {
        "status": "otp_sent",
        "show_verification": True,
        "temp_email": payload.email,
        "message": f"An OTP has been sent to {payload.email} (Use 1234 for testing).",
    }


@router.post("/auth/verify-otp")
async def verify_merchant_otp(payload: AuthVerifyOTPRequest):
    """Verifies the 4-digit OTP ('1234') and logs the user in."""
    if payload.otp != "1234":
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    user = verify_account(payload.email)
    username = user["username"] if user else "New User"
    user_id = user["user_id"] if user else str(uuid.uuid4())
    token = _issue_jwt_for_user(user_id, username)

    return {
        "status": "success",
        "logged_in": True,
        "username": username,
        "email": payload.email,
        "access_token": token,
        "org_id": DEFAULT_ORG_ID,
    }


# =====================================================================
# 1. LIVE MARKET TERMINAL 🔴
# =====================================================================
@router.get("/market/terminal")
async def get_live_market_terminal(
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Returns Market Heat, Buyer Mood, Avg. Profit, High Demand Gainers, and Slow Moving Losers."""
    return get_live_market_terminal_snapshot()


@router.post("/market/arbitrage-scan")
async def run_live_scraper_and_arbitrage(
    payload: ArbitrageScanRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Scrapes real-time retail prices from BD E-commerce (StarTech) and runs AI Quant Models
    (generate_math_prediction) to compute wholesale vs retail arbitrage.
    """
    retail_items = scrape_real_retail_data(
        category=payload.category,
        attempt_network=payload.attempt_network,
    )
    results: List[Dict[str, Any]] = []
    for item in retail_items:
        retail_bdt = float(item["retail_price"])
        wholesale_bdt = int(retail_bdt * payload.assumed_wholesale_discount)
        insert_price_data(item["product_name"], retail_bdt)
        quant = generate_math_prediction(item["product_name"], wholesale_bdt, retail_bdt)
        results.append(quant)

    return {
        "status": "success",
        "message": "✅ Live Data Fetched!",
        "category": payload.category,
        "assumed_wholesale_discount": payload.assumed_wholesale_discount,
        "opportunities": results,
    }


# =====================================================================
# 2. MACRO & MICRO MARKET OVERVIEW 🌍
# =====================================================================
@router.get("/market/overview")
async def get_macro_micro_market_overview(
    fetch_live: bool = Query(default=False),
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Returns National Sector Pulse & Volume, Live USD/BDT Rate with Sparkline,
    Global Economic Indicators (Gold, Crude Oil, S&P 500), and Live Local Inventory (Private Wallet).
    """
    return {
        "national_pulse": get_national_market_pulse(),
        "usd_rate": get_live_usd_rate(fetch_live=fetch_live),
        "global_indicators": get_global_indicators(fetch_live=fetch_live),
        "private_wallet": get_wallet_inventory(),
    }


@router.post("/market/live-product-price")
async def check_live_product_price(
    payload: LiveProductPriceRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Scrapes live product price from a StarTech product page."""
    price = get_live_product_price(payload.url)
    return {
        "url": payload.url,
        "live_price": price,
        "status": "FOUND" if price else "FALLBACK",
        "fallback_price": price or 145000,
    }


# =====================================================================
# 3. SUPPLIER TRUST RADAR 🛡️ (SME GUARDIAN)
# =====================================================================
@router.get("/suppliers/trust-radar")
async def get_trust_radar_endpoint(
    search: Optional[str] = Query(default=None, description="Search Wholesaler Name or Location"),
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Returns crowdsourced memo price consistency Trust Scores for Top Verified Titans
    and Red Flag / Scam Alerts.
    """
    return get_supplier_trust_radar(search_query=search)


# =====================================================================
# 4. AI PRODUCT & TREND ANALYTICS 📦 (THE FLYWHEEL)
# =====================================================================
@router.get("/analytics/flywheel")
async def get_product_and_trend_analytics(
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Returns all 3 tabs of AI Product & Trend Analytics:
    1. My Ledger Analytics
    2. Community Trends & Price Benchmark (You vs Market)
    3. Proactive AI Alerts (Stockout Risk & Capital Liquidity Alert)
    """
    return get_flywheel_analytics()


@router.post("/analytics/market-insight")
async def generate_market_insight_endpoint(
    payload: MarketInsightRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Generates 3-bullet market insight using Groq (Llama 3.1) or Gemini 2.5 Flash."""
    insight = get_market_insight(
        product_name=payload.product_name,
        current_price=payload.current_price,
        usd_rate=payload.usd_rate,
        preferred_model=payload.preferred_model,
    )
    return {
        "product_name": payload.product_name,
        "preferred_model": payload.preferred_model,
        "insight_markdown": insight,
    }


@router.post("/analytics/product-insight")
async def generate_product_insight_endpoint(
    payload: ProductInsightRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Generates dual-perspective intelligence report for Current Stock Holders & New Entrepreneurs."""
    history = get_product_history(payload.product_name) or get_price_history(payload.product_name)
    report = generate_product_insight(payload.product_name, history)
    return {
        "product_name": payload.product_name,
        "history_records": len(history),
        "report_markdown": report,
    }


# =====================================================================
# 5. SAFE INVESTMENT GUIDE 🛡️ (AI CAPITAL SHIELD & RISK SIMULATOR)
# =====================================================================
@router.get("/risk/context")
async def get_risk_context_endpoint(
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Returns scanned products and auto-pilot slider defaults calculated from sales_ledger due ratio."""
    return get_risk_simulator_context()


@router.post("/risk/simulate")
async def simulate_risk_endpoint(
    payload: RiskSimulationRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Calculates safe inventory sizing, simulated profit/loss, AI Risk Meter (0-100), and Guard Alerts."""
    return simulate_capital_risk(
        capital=payload.capital,
        selected_asset=payload.selected_asset,
        capital_usage_pct=payload.capital_usage_pct,
        markup_pct=payload.markup_pct,
        price_change_pct=payload.price_change_pct,
    )


# =====================================================================
# 6. START NEW BUSINESS 🚀 (BUSINESS IDEA VALIDATOR)
# =====================================================================
@router.post("/validator/idea")
async def validate_business_idea_endpoint(
    payload: IdeaValidationRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Generates a comprehensive Market Feasibility Report for starting a gadget/SME business."""
    return generate_idea_validation(
        location=payload.location,
        category=payload.category,
        business_model=payload.business_model,
        budget=payload.budget,
        margin=payload.margin,
        risk=payload.risk,
    )


# =====================================================================
# 7. SMART MEMO SCANNER 📸 & WHOLESALE STOCK ENTRY
# =====================================================================
@router.post("/scanner/extract-image")
async def extract_wholesale_memo_image(
    payload: ImageMemoExtractRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Extracts wholesale purchase items from an uploaded memo image."""
    img_bytes = b""
    if payload.image_base64:
        raw_b64 = payload.image_base64.split(",")[-1]
        try:
            img_bytes = base64.b64decode(raw_b64)
        except Exception:
            img_bytes = b""

    extracted = extract_data_from_memo(img_bytes, mime_type=payload.mime_type)
    return {
        "status": "extracted",
        "source": "image_memo",
        "temp_purchase": extracted,
    }


@router.post("/scanner/extract-voice")
async def extract_wholesale_voice_purchase(
    payload: VoiceExtractRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Extracts wholesale purchase details from an audio file or live voice recording."""
    if payload.transcript_hint:
        extracted = extract_purchase_or_order_from_text(payload.transcript_hint, mode="scanner")
    else:
        audio_bytes = b""
        if payload.audio_base64:
            raw_b64 = payload.audio_base64.split(",")[-1]
            try:
                audio_bytes = base64.b64decode(raw_b64)
            except Exception:
                audio_bytes = b""
        extracted = extract_sales_from_audio(audio_bytes, mime_type=payload.mime_type)

    return {
        "status": "extracted",
        "source": "voice_purchase",
        "temp_purchase": extracted,
    }


@router.post("/scanner/extract-text")
async def extract_wholesale_text_purchase(
    payload: TextExtractRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Extracts wholesale purchase details from bulk text message with exponential backoff retry."""
    extracted = extract_purchase_or_order_from_text(payload.text, mode="scanner")
    return {
        "status": "extracted",
        "source": "text_purchase",
        "temp_purchase": extracted,
    }


@router.post("/scanner/commit-inventory")
async def commit_purchase_to_inventory(
    payload: InventoryCommitRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Commits reviewed/edited single or batch items into memo_tracker ('Stock Added').
    Mirrors legacy-streamlit-mvp/app.py lines 521-557.
    """
    items_dicts = [item.model_dump() for item in payload.items]
    total_units = commit_inventory_items(items_dicts)
    return {
        "status": "committed",
        "total_units_added": total_units,
        "distinct_items": len(items_dicts),
        "message": f"✅ ইনভেন্টরিতে মোট {total_units} পিস স্টক সেভ করা হয়েছে!",
        "live_inventory": get_live_inventory(),
    }


# =====================================================================
# 8. ORDER INBOX 📥 & CUSTOMER DUES LEDGER (WHATSAPP SALES LEDGER)
# =====================================================================
@router.post("/orders/extract-voice")
async def extract_order_voice_endpoint(
    payload: VoiceExtractRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Extracts customer order details from voice note with silent manual-entry fallback
    matching legacy-streamlit-mvp/app.py lines 1138-1191.
    """
    if payload.transcript_hint:
        extracted = extract_purchase_or_order_from_text(payload.transcript_hint, mode="ledger")
    else:
        audio_bytes = b""
        if payload.audio_base64:
            raw_b64 = payload.audio_base64.split(",")[-1]
            try:
                audio_bytes = base64.b64decode(raw_b64)
            except Exception:
                audio_bytes = b""
        extracted = extract_sales_from_audio(audio_bytes, mime_type=payload.mime_type)

    return {
        "status": "extracted",
        "order_source": "ledger",
        "temp_order": extracted,
    }


@router.post("/orders/extract-text")
async def extract_order_text_endpoint(
    payload: TextExtractRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Extracts customer order details from WhatsApp text message with silent manual-entry fallback
    matching legacy-streamlit-mvp/app.py lines 1194-1233.
    """
    extracted = extract_purchase_or_order_from_text(payload.text, mode="ledger")
    return {
        "status": "extracted",
        "order_source": "ledger",
        "temp_order": extracted,
    }


@router.post("/orders/confirm", status_code=status.HTTP_201_CREATED)
async def confirm_and_save_order_to_ledger(
    payload: ConfirmOrderRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Saves reviewed/edited order into sales_ledger and generates the Trade Wolf Smart Receipt
    matching legacy-streamlit-mvp/app.py lines 1257-1314.
    """
    t_bill = float(payload.quantity) * float(payload.unit_price)
    t_due = max(0.0, t_bill - float(payload.paid_amount))

    row_id = record_new_sale(
        customer=payload.customer_name,
        item=payload.item_name,
        qty=payload.quantity,
        unit_price=payload.unit_price,
        total_bill=t_bill,
        paid=payload.paid_amount,
        due=t_due,
    )

    date_str = time.strftime("%Y-%m-%d")
    invoice_data = (
        f"🐺 TRADE WOLF RECEIPT\n"
        f"-----------------------\n"
        f"Customer: {payload.customer_name}\n"
        f"Item: {payload.item_name} (x{payload.quantity})\n"
        f"-----------------------\n"
        f"Total Bill: ৳{t_bill:,.0f}\n"
        f"Paid: ৳{payload.paid_amount:,.0f}\n"
        f"Due: ৳{t_due:,.0f}\n"
        f"-----------------------\n"
        f"Powered by Trade Wolf AI"
    )

    smart_receipt = (
        f"🐺 TRADE WOLF SMART RECEIPT 🐺\n"
        f"-------------------------------\n"
        f"Customer: {payload.customer_name}\n"
        f"Date: {date_str}\n"
        f"-------------------------------\n"
        f"Item: {payload.item_name}\n"
        f"Qty: {payload.quantity} @ ৳{payload.unit_price:,.0f}\n"
        f"-------------------------------\n"
        f"Total Bill: ৳{t_bill:,.0f}\n"
        f"Cash Paid: ৳{payload.paid_amount:,.0f}\n"
        f"DUE AMOUNT: ৳{t_due:,.0f}\n"
        f"-------------------------------\n"
        f"Generated by: Trade Wolf AI"
    )

    return {
        "status": "saved",
        "id": row_id,
        "customer_name": payload.customer_name,
        "item_name": payload.item_name,
        "quantity": payload.quantity,
        "unit_price": payload.unit_price,
        "total_bill": t_bill,
        "paid_amount": payload.paid_amount,
        "due_amount": t_due,
        "invoice_data": invoice_data,
        "smart_receipt": smart_receipt,
        "filename": f"Memo_{payload.customer_name.replace(' ', '_')}.txt",
    }


@router.get("/orders/ledger")
async def get_customer_dues_ledger(
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """Returns Total Dues, Cash Collected, cleaned Sales Ledger table, and customers with pending dues."""
    return get_all_sales()


@router.post("/orders/draft-reminder")
async def draft_customer_due_reminder(
    payload: DraftReminderRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Drafts the dynamic Banglish WhatsApp due recovery message and wa.me link
    matching legacy-streamlit-mvp/app.py lines 1351-1367.
    """
    sales_data = get_all_sales()
    target = payload.customer_name
    customer_due = 0.0

    for row in sales_data["rows"]:
        if row["customer"].lower() == target.lower() and row["due"] > 0:
            customer_due += float(row["due"])

    if customer_due <= 0:
        customer_due = 1500.0

    drafted_msg = (
        f"Assalamu Alaikum {target}, apnar ৳{customer_due:,.0f} due baki ache. "
        f"Ektu taratari clear korle upokar hoto. Dhonnobad!"
    )
    encoded_msg = urllib.parse.quote(drafted_msg)
    whatsapp_link = f"https://wa.me/?text={encoded_msg}"

    return {
        "customer_name": target,
        "total_due": customer_due,
        "drafted_message": drafted_msg,
        "whatsapp_link": whatsapp_link,
    }


# =====================================================================
# 9. DOCUMENT CHAT AI 📄 (RAG REPORT ANALYSIS)
# =====================================================================
@router.post("/rag/process-document")
async def process_rag_document_endpoint(
    payload: RAGProcessDocumentRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Extracts text from an uploaded PDF or CSV document and builds the SKLearn/Cosine Vector Store.
    Mirrors legacy-streamlit-mvp/app.py lines 1078-1098 & document_ai.py.
    """
    raw_text = payload.raw_text or ""
    if not raw_text and payload.file_base64:
        raw_b64 = payload.file_base64.split(",")[-1]
        try:
            file_bytes = base64.b64decode(raw_b64)
            raw_text = extract_text_from_file_bytes(file_bytes, payload.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse document bytes: {e}")

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Uploaded document appears to be empty.")

    return build_rag_index(org_id=x_org_id, filename=payload.filename, raw_text=raw_text)


@router.post("/rag/chat")
async def chat_with_rag_document_endpoint(
    payload: RAGChatRequest,
    x_org_id: str = Header(default=DEFAULT_ORG_ID),
):
    """
    Queries the vector store and generates a grounded response using Groq (Fast & Free) or Gemini.
    Mirrors legacy-streamlit-mvp/app.py lines 1099-1118 & document_ai.py.
    """
    answer = analyze_report_with_ai(
        org_id=x_org_id,
        query=payload.query,
        model_choice=payload.model_choice,
    )
    return {
        "query": payload.query,
        "model_choice": payload.model_choice,
        "answer": answer,
    }

