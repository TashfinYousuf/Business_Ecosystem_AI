-- backend/database/migrations/002_sync_ledger.sql
-- Cloud Deduplication Ledger & Idempotency Store for Postgres

CREATE TABLE IF NOT EXISTS sync_inbound_ledger (
    idempotency_key VARCHAR(128) PRIMARY KEY,
    org_id UUID NOT NULL,
    table_name VARCHAR(64) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(16) NOT NULL,
    client_version INT NOT NULL,
    client_timestamp TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(32) NOT NULL DEFAULT 'APPLIED',
    conflict_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolution_strategy VARCHAR(64) DEFAULT 'LAST_WRITE_WINS'
);

CREATE INDEX IF NOT EXISTS idx_sync_inbound_org_table 
ON sync_inbound_ledger(org_id, table_name, record_id);