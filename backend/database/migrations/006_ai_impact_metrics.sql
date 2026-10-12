-- backend/database/migrations/006_ai_impact_metrics.sql
-- AI Value Attribution Ledger & ROI Metrics Schema

CREATE TABLE IF NOT EXISTS ai_impact_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    category VARCHAR(32) NOT NULL 
        CHECK(category IN ('TIME_SAVED', 'DEBT_RECOVERED', 'CALCULATION_ERROR_CAUGHT', 'DEADSTOCK_AVOIDED')),
    source_reference_id UUID, -- Links to invoice_id, memo_id, or reminder_log_id
    hours_saved NUMERIC(6, 2) NOT NULL DEFAULT 0.00,
    monetary_value_bdt NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    description TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_impact_org_category 
ON ai_impact_events(org_id, category, created_at DESC);

-- Aggregated Summary Table for fast dashboard querying
CREATE TABLE IF NOT EXISTS ai_impact_summaries (
    org_id UUID PRIMARY KEY,
    total_hours_saved NUMERIC(8, 2) NOT NULL DEFAULT 0.00,
    total_debt_recovered_bdt NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    total_math_errors_fixed INT NOT NULL DEFAULT 0,
    estimated_cost_saved_bdt NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);