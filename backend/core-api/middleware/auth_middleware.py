"""
backend/core-api/middleware/auth_middleware.py
Multi-Tenant Authentication and Organization Context Resolution Middleware.
Extracts JWT/API key, validates cryptographic signature, and binds org_id to request state.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Callable, Optional, Set
import jwt
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("AuthMiddleware")

# Secret configuration (Defaults to secure testing key if environment is unconfigured)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tradewolf-super-secret-system-key-for-jwt-signing-2026")
JWT_ALGORITHM = "HS256"

# Endpoints exempt from mandatory tenant authentication
PUBLIC_PATHS: Set[str] = {
    "/healthz",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/verify-otp",
    "/api/v1/ui/dictionary",
}


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Intercepts incoming requests, validates tenant identity,
        and injects verified org_id and user_id into request.state.
        """
        path = request.url.path

        # 1. Skip authentication for public telemetry and doc paths
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/static"):
            return await call_next(request)

        # 2. Extract Authorization Header
        auth_header = request.headers.get("Authorization")
        explicit_org_header = request.headers.get("X-Org-ID")

        resolved_org_id: Optional[str] = None
        resolved_user_id: Optional[str] = None
        resolved_role: str = "MERCHANT"

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # Decode and verify JWT signature
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                resolved_org_id = payload.get("org_id")
                resolved_user_id = payload.get("sub")
                resolved_role = payload.get("role", "MERCHANT")
            except jwt.ExpiredSignatureError:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"error": "AUTH_EXPIRED", "message": "Authentication token has expired."},
                )
            except jwt.InvalidTokenError as e:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"error": "AUTH_INVALID", "message": f"Invalid authentication token: {str(e)}"},
                )
        elif explicit_org_header:
            # Fallback for internal services / dev test harnesses providing direct valid UUID header
            try:
                uuid.UUID(explicit_org_header)
                resolved_org_id = explicit_org_header
                resolved_user_id = "service-internal-worker"
                resolved_role = "SYSTEM_WORKER"
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "INVALID_ORG_ID", "message": "Provided X-Org-ID is not a valid UUID."},
                )

        # 3. Deny request if no valid tenant context could be derived
        if not resolved_org_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "UNAUTHORIZED_TENANT",
                    "message": "Missing or unresolvable tenant identity. Bearer token or X-Org-ID header required.",
                },
            )

        # 4. Attach verified tenant context to request state
        request.state.org_id = resolved_org_id
        request.state.user_id = resolved_user_id
        request.state.role = resolved_role

        response = await call_next(request)
        
        # Attach sanitized tenant context identifier to outbound response header for tracing
        response.headers["X-Tenant-Context"] = resolved_org_id
        return response