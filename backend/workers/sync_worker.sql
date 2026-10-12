"""
backend/workers/sync_worker.py
Deterministic Offline-to-Cloud Sync Engine for Trade Wolf OS.
Handles bi-directional batch reconciliation, idempotency guarantees, and conflict resolution.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SyncWorker")


@dataclass
class SyncRecord:
    id: str
    org_id: str
    table_name: str
    record_id: str
    operation: str
    payload: Dict[str, Any]
    idempotency_key: str
    client_version: int
    client_timestamp: str
    retry_count: int


class DeterministicSyncEngine:
    def __init__(self, sqlite_path: str, pg_conn_string: str, batch_size: int = 50):
        self.sqlite_path = sqlite_path
        self.pg_conn_string = pg_conn_string
        self.batch_size = batch_size

    def _get_sqlite_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_pg_conn(self):
        return psycopg2.connect(self.pg_conn_string)

    def fetch_pending_outbox_batch(self) -> List[SyncRecord]:
        """Fetch un-synced operations queued in local SQLite outbox."""
        query = """
            SELECT id, org_id, table_name, record_id, operation, payload, 
                   idempotency_key, client_version, client_timestamp, retry_count
            FROM sync_outbox
            WHERE status IN ('PENDING', 'FAILED') AND retry_count < 5
            ORDER BY created_at ASC
            LIMIT ?;
        """
        with self._get_sqlite_conn() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query, (self.batch_size,)).fetchall()
            records = []
            for r in rows:
                records.append(
                    SyncRecord(
                        id=r["id"],
                        org_id=r["org_id"],
                        table_name=r["table_name"],
                        record_id=r["record_id"],
                        operation=r["operation"],
                        payload=json.loads(r["payload"]),
                        idempotency_key=r["idempotency_key"],
                        client_version=r["client_version"],
                        client_timestamp=r["client_timestamp"],
                        retry_count=r["retry_count"],
                    )
                )
            return records

    def process_outbox_push(self) -> int:
        """
        Pushes outbox mutations to Cloud PostgreSQL inside atomic transactions.
        Applies idempotency check and Last-Write-Wins (LWW) conflict strategy.
        """
        records = self.fetch_pending_outbox_batch()
        if not records:
            return 0

        logger.info("Found %d pending outbox records to sync.", len(records))

        try:
            pg_conn = self._get_pg_conn()
        except Exception as e:
            logger.warning("Cloud Postgres unreachable (offline). Error: %s", str(e))
            return 0

        synced_ids: List[str] = []
        failed_records: Dict[str, str] = {}

        try:
            with pg_conn:
                with pg_conn.cursor(cursor_factory=RealDictCursor) as pg_cursor:
                    for record in records:
                        try:
                            # 1. Idempotency Check
                            pg_cursor.execute(
                                "SELECT status FROM sync_inbound_ledger WHERE idempotency_key = %s;",
                                (record.idempotency_key,),
                            )
                            existing = pg_cursor.fetchone()
                            if existing:
                                logger.info("Duplicate idempotency key %s skipped.", record.idempotency_key)
                                synced_ids.append(record.id)
                                continue

                            # 2. Conflict & Version Resolution (Last-Write-Wins via timestamp/version)
                            # Verify if target record exists on server
                            pg_cursor.execute(
                                f"SELECT updated_at, org_id FROM {record.table_name} WHERE id = %s;",
                                (record.record_id,),
                            )
                            server_row = pg_cursor.fetchone()

                            if server_row:
                                server_ts = server_row["updated_at"].isoformat()
                                client_ts = record.client_timestamp
                                # Conflict Detection: If server timestamp is ahead of local client change
                                if server_ts > client_ts:
                                    logger.warning(
                                        "Conflict on %s (ID %s). Server TS %s > Client TS %s. Dropping client mutation.",
                                        record.table_name,
                                        record.record_id,
                                        server_ts,
                                        client_ts,
                                    )
                                    self._record_ledger_entry(
                                        pg_cursor, record, status="CONFLICT_REJECTED", conflict=True
                                    )
                                    synced_ids.append(record.id)
                                    continue

                            # 3. Apply Operation
                            self._apply_operation(pg_cursor, record)

                            # 4. Record to sync inbound ledger
                            self._record_ledger_entry(pg_cursor, record, status="APPLIED", conflict=False)
                            synced_ids.append(record.id)

                        except Exception as op_err:
                            logger.error("Failed processing record %s: %s", record.id, str(op_err))
                            failed_records[record.id] = str(op_err)

            # Update Local SQLite statuses
            self._update_local_status(synced_ids, failed_records)

        finally:
            pg_conn.close()

        return len(synced_ids)

    def _apply_operation(self, cursor, record: SyncRecord) -> None:
        """Applies dynamic SQL mutations safely to Postgres."""
        table = record.table_name
        payload = record.payload

        if record.operation == "INSERT":
            columns = list(payload.keys())
            placeholders = ["%s"] * len(columns)
            query = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (id) DO UPDATE 
                SET {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'])};
            """
            cursor.execute(query, list(payload.values()))

        elif record.operation == "UPDATE":
            set_clauses = [f"{col} = %s" for col in payload.keys() if col != "id"]
            values = [val for col, val in payload.items() if col != "id"]
            values.append(record.record_id)
            query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = %s;"
            cursor.execute(query, values)

        elif record.operation == "DELETE":
            query = f"DELETE FROM {table} WHERE id = %s;"
            cursor.execute(query, (record.record_id,))

    def _record_ledger_entry(self, cursor, record: SyncRecord, status: str, conflict: bool) -> None:
        """Logs processed message in cloud sync_inbound_ledger."""
        cursor.execute(
            """
            INSERT INTO sync_inbound_ledger 
            (idempotency_key, org_id, table_name, record_id, operation, client_version, client_timestamp, status, conflict_resolved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                record.idempotency_key,
                record.org_id,
                record.table_name,
                record.record_id,
                record.operation,
                record.client_version,
                record.client_timestamp,
                status,
                conflict,
            ),
        )

    def _update_local_status(self, synced_ids: List[str], failed_records: Dict[str, str]) -> None:
        """Flushes sync results back into local SQLite outbox."""
        with self._get_sqlite_conn() as conn:
            cursor = conn.cursor()
            if synced_ids:
                placeholders = ",".join(["?"] * len(synced_ids))
                cursor.execute(
                    f"UPDATE sync_outbox SET status = 'SYNCED', updated_at = datetime('now', 'utc') WHERE id IN ({placeholders})",
                    synced_ids,
                )

            for rec_id, error_msg in failed_records.items():
                cursor.execute(
                    """
                    UPDATE sync_outbox 
                    SET status = 'FAILED', retry_count = retry_count + 1, last_error = ?, updated_at = datetime('now', 'utc')
                    WHERE id = ?;
                    """,
                    (error_msg, rec_id),
                )
            conn.commit()


if __name__ == "__main__":
    # Test runner loop demo
    engine = DeterministicSyncEngine(
        sqlite_path="local_edge_trade_wolf.db",
        pg_conn_string="postgresql://tradewolf:tradewolf_secret@localhost:5432/tradewolf_db",
    )
    processed = engine.process_outbox_push()
    logger.info("Sync iteration completed. Successfully reconciled: %d items.", processed)