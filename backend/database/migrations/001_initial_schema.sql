-- ============================================================================
-- TRADE WOLF OS: MULTI-TENANT PRODUCTION DATABASE SCHEMA
-- Target Engine: PostgreSQL 16+ with pgvector
-- Tenant Boundary: org_id on all operational tables
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ----------------------------------------------------------------------------
-- 1. IAM & TENANCY (Organizations, Users, Roles)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    trade_license VARCHAR(100),
    business_type VARCHAR(50) DEFAULT 'importer_wholesaler',
    subscription_tier VARCHAR(50) DEFAULT 'free',
    currency VARCHAR(10) DEFAULT 'BDT',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50) NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'owner', -- 'owner', 'manager', 'cashier', 'auditor'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_org ON users(org_id);

-- ----------------------------------------------------------------------------
-- 2. OPERATE (Products, Inventory Batches, Suppliers)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    hub_location VARCHAR(100), -- 'Chawkbazar', 'Khatungonj', 'International'
    reliability_score NUMERIC(5,2) DEFAULT 100.00,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_suppliers_org ON suppliers(org_id);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100),
    category VARCHAR(100),
    default_wholesale_price NUMERIC(15,2) DEFAULT 0.00,
    default_retail_price NUMERIC(15,2) DEFAULT 0.00,
    min_stock_alert INTEGER DEFAULT 5,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_products_org ON products(org_id);

CREATE TABLE IF NOT EXISTS inventory_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    cost_price NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    source VARCHAR(50) DEFAULT 'manual', -- 'memo_scan', 'voice', 'manual'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_inventory_org_product ON inventory_batches(org_id, product_id);

-- ----------------------------------------------------------------------------
-- 3. SALES, CUSTOMERS & DUE LEDGER
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    trust_score NUMERIC(5,2) DEFAULT 100.00,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_customers_org ON customers(org_id);

CREATE TABLE IF NOT EXISTS sales_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    customer_name VARCHAR(255) NOT NULL, -- snapshot
    item_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    total_bill NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    paid_amount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    due_amount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    order_source VARCHAR(50) DEFAULT 'text_order', -- 'voice', 'text', 'manual', 'network'
    raw_ai_input TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sales_ledger_org ON sales_ledger(org_id);
CREATE INDEX idx_sales_ledger_due ON sales_ledger(org_id, due_amount);

-- ----------------------------------------------------------------------------
-- 4. OFFLINE SYNC ENGINE & IDEMPOTENCY
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sync_operations_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    device_id VARCHAR(100) NOT NULL,
    idempotency_key VARCHAR(120) UNIQUE NOT NULL,
    entity_name VARCHAR(100) NOT NULL, -- 'sales_ledger', 'inventory_batches'
    operation_type VARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    payload JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'applied', -- 'applied', 'conflict_resolved', 'failed'
    synced_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sync_idempotency ON sync_operations_log(idempotency_key);

-- ----------------------------------------------------------------------------
-- 5. AI CONTROL PLANE & AEGIS SENTINEL LOGS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL, -- 'CollectionsAgent', 'ProcurementAgent'
    action_type VARCHAR(100) NOT NULL,
    prompt_metadata JSONB,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost_estimated NUMERIC(10,6) DEFAULT 0.00,
    security_verdict VARCHAR(50) DEFAULT 'ALLOWED', -- 'ALLOWED', 'BLOCKED_BY_AEGIS'
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_agent_audit_org ON agent_audit_logs(org_id);

-- ----------------------------------------------------------------------------
-- 6. ROW LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_operations_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_audit_logs ENABLE ROW LEVEL SECURITY;

-- Tenant Isolation RLS Policy Helper
-- JWT Token theke org_id read korbe: current_setting('app.current_org_id', true)::uuid
CREATE POLICY org_isolation_products ON products
    USING (org_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid);

CREATE POLICY org_isolation_sales ON sales_ledger
    USING (org_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid);

CREATE POLICY org_isolation_inventory ON inventory_batches
    USING (org_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid);