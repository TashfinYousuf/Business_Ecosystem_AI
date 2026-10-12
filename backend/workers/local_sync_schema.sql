-- backend/workers/local_sync_schema.sql
-- Offline-First Outbox Log & Shadow Table Schema for Local Edge Device (SQLite 3)

PRAGMA foreign_keys = ON;

-- 1. Sync Outbox Queue: Captures transactional mutations locally
CREATE TABLE IF NOT EXISTS sync_outbox (
    id TEXT PRIMARY KEY,                       -- UUID v4 generated locally
    org_id TEXT NOT NULL,                      -- Multi-tenant context
    table_name TEXT NOT NULL,                  -- Target PostgreSQL table
    record_id TEXT NOT NULL,                   -- Primary key of the modified record
    operation TEXT NOT NULL CHECK(operation IN ('INSERT', 'UPDATE', 'DELETE')),
    payload TEXT NOT NULL,                     -- Serialized JSON snapshot of the mutation
    idempotency_key TEXT NOT NULL UNIQUE,      -- SHA256(org_id + table + record_id + client_version)
    client_version INTEGER NOT NULL DEFAULT 1, -- Optimistic concurrency counter per record
    client_timestamp TEXT NOT NULL,            -- ISO8601 UTC timestamp of creation
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'PROCESSING', 'SYNCED', 'FAILED', 'CONFLICT')),
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_sync_outbox_status_retries 
ON sync_outbox(status, retry_count, created_at);

-- 2. Local State Management for Sync Metadata & Inbound Cursor
CREATE TABLE IF NOT EXISTS sync_state (
    table_name TEXT PRIMARY KEY,
    last_pulled_server_checkpoint TEXT NOT NULL DEFAULT '1970-01-01T00:00:00.000Z',
    last_sync_attempt TEXT,
    is_locked INTEGER NOT NULL DEFAULT 0
);