"""
backend/core-api/auth_utils.py
Cryptographic JWT utilities and security primitives for Trade Wolf OS authentication.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tradewolf-os-super-secret-production-grade-key-2026")
TOKEN_EXPIRY_SECONDS = 86400 * 7  # 7 days


@dataclass
class TokenPayload:
    user_id: str
    org_id: str
    role: str  # "OWNER", "MANAGER", "CASHIER"
    exp: int


def _base64url_encode(data: bytes) -> str:
    """Encodes bytes into a URL-safe Base64 string without padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64url_decode(data: str) -> bytes:
    """Decodes a URL-safe Base64 string adding back necessary padding."""
    padding = "=" * (4 - (len(data) % 4)) if len(data) % 4 != 0 else ""
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(user_id: str, org_id: str, role: str = "OWNER") -> str:
    """Creates a deterministic HS256-signed JWT token without heavy external dependencies."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "user_id": user_id,
        "org_id": org_id,
        "role": role,
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
    }

    header_b64 = _base64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(payload).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> TokenPayload:
    """
    Decodes and validates JWT authenticity and signature.
    Raises ValueError on token tampering, malformation, or expiry.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Malformed token format.")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    received_sig = _base64url_decode(sig_b64)

    if not hmac.compare_digest(expected_sig, received_sig):
        raise ValueError("Invalid cryptographic token signature.")

    payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))

    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("Token has expired.")

    return TokenPayload(
        user_id=payload["user_id"],
        org_id=payload["org_id"],
        role=payload.get("role", "OWNER"),
        exp=payload["exp"],
    )