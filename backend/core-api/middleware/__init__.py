# backend/core-api/middleware/__init__.py
"""
backend/core-api/middleware/__init__.py
Exports authentication and tenant context middleware.
"""

from .auth_middleware import TenantContextMiddleware, JWT_SECRET_KEY, JWT_ALGORITHM

__all__ = ["TenantContextMiddleware", "JWT_SECRET_KEY", "JWT_ALGORITHM"]