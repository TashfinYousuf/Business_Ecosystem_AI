"""
backend/core-api/database.py
PostgreSQL connection pool & context-bound session dependency with strict RLS enforcement.
Applies 'SET LOCAL app.current_org_id' per transaction.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import Depends, Request, HTTPException

logger = logging.getLogger("DatabaseSession")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://tradewolf:tradewolf_secret@localhost:5432/tradewolf_db"
)


class DatabaseManager:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def get_connection(self):
        """Creates a direct database connection."""
        return psycopg2.connect(self.dsn)


db_manager = DatabaseManager(DATABASE_URL)


def get_tenant_db_connection(request: Request) -> Generator[psycopg2.extensions.connection, None, None]:
    """
    FastAPI dependency yielding a connection strictly isolated to the caller's org_id.
    Executes PostgreSQL 'SET LOCAL app.current_org_id' inside the transaction.
    """
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="Security violation: Missing tenant context in DB layer.")

    conn = db_manager.get_connection()
    try:
        # Enforce Row-Level Security context for current transaction
        with conn.cursor() as cursor:
            cursor.execute("SET LOCAL app.current_org_id = %s;", (org_id,))
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("Database transaction rolled back for org %s: %s", org_id, str(e))
        raise
    finally:
        conn.close()