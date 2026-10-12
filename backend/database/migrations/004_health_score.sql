-- backend/database/migrations/004_health_score.sql
-- Business Health Score & Stability Metric History Schema

CREATE TABLE IF NOT EXISTS business_health_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    total_score NUMERIC(5, 2) NOT NULL CHECK(total_score >= 0 AND total_score <= 100),
    health_band VARCHAR(24) NOT NULL CHECK(health_band IN ('CRITICAL', 'FRAGILE', 'MODERATE', 'ROBUST')),
    
    -- Metric Sub-component breakdown (Weighted 0-100 each)
    cash_flow_liquidity_score NUMERIC(5, 2) NOT NULL,
    debt_burden_ratio_score NUMERIC(5, 2) NOT NULL,
    inventory_velocity_score NUMERIC(5, 2) NOT NULL,
    customer_retention_score NUMERIC(5, 2) NOT NULL,
    margin_stability_score NUMERIC(5, 2) NOT NULL,
    
    -- Absolute telemetry metrics for SME audit
    total_receivable_due NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    total_monthly_revenue NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    deadstock_item_count INT NOT NULL DEFAULT 0,
    
    insights JSONB NOT NULL DEFAULT '[]'::jsonb,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_snapshots_org_date 
ON business_health_snapshots(org_id, calculated_at DESC);