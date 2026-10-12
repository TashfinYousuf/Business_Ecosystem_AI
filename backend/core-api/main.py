"""
backend/core-api/main.py
Main entry point for Trade Wolf OS Core Business API.
Integrated with dynamic sys.path anchoring and TenantContextMiddleware.
"""

from __future__ import annotations

import os
import sys
import logging

# Ensure local core-api modules resolve safely regardless of working directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from middleware.auth_middleware import TenantContextMiddleware
from routes.business_routes import router as business_router
from routes.legacy_ecosystem_routes import router as legacy_ecosystem_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TradeWolfAPI")

app = FastAPI(
    title="Trade Wolf OS - Core Business API",
    description="Deterministic AI-Native Commerce Operating System for Emerging Markets",
    version="0.11.0",
)

# 1. Register Tenant Context & Authentication Middleware
app.add_middleware(TenantContextMiddleware)

# 2. Register CORS Middleware for Web & Mobile Clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Tenant-Context"],
)

# 3. Include Business Operations & Legacy Ecosystem Routers
app.include_router(business_router)
app.include_router(legacy_ecosystem_router)


@app.get("/healthz", tags=["System Status"])
async def health_check():
    """Public system heartbeat check (Bypasses auth middleware)."""
    return {
        "status": "ONLINE",
        "service": "Trade Wolf OS Core API",
        "engine_version": "0.11.0",
        "multi_tenancy": "ENFORCED",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)