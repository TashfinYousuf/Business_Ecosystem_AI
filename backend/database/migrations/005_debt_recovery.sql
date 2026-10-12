-- backend/database/migrations/005_debt_recovery.sql
-- Debt Recovery Pipeline & Customer Engagement Tracking Schema

-- 1. Ongoing Debt Cases grouped by customer
CREATE TABLE IF NOT EXISTS debt_recovery_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    total_due_amount NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    oldest_due_date DATE NOT NULL,
    aging_bucket VARCHAR(16) NOT NULL CHECK(aging_bucket IN ('CURRENT', '1_15_DAYS', '16_30_DAYS', '31_60_DAYS', 'OVER_60_DAYS')),
    risk_level VARCHAR(16) NOT NULL DEFAULT 'LOW' CHECK(risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'SEVERE')),
    status VARCHAR(24) NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'PARTIALLY_SETTLED', 'SETTLED', 'WRITTEN_OFF')),
    last_contacted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_debt_cases_org_bucket 
ON debt_recovery_cases(org_id, aging_bucket, status);

-- 2. Reminder Dispatch & Action Log
CREATE TABLE IF NOT EXISTS debt_reminder_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES debt_recovery_cases(id) ON DELETE CASCADE,
    org_id UUID NOT NULL,
    tone VARCHAR(16) NOT NULL CHECK(tone IN ('GENTLE', 'MODERATE', 'FIRM', 'URGENT')),
    channel VARCHAR(16) NOT NULL DEFAULT 'WHATSAPP' CHECK(channel IN ('WHATSAPP', 'SMS')),
    message_body TEXT NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'PENDING_APPROVAL' CHECK(status IN ('PENDING_APPROVAL', 'APPROVED', 'DISPATCHED', 'REJECTED', 'DELIVERY_FAILED')),
    approval_request_id UUID,
    dispatched_at TIMESTAMPTZ,
    recovered_amount NUMERIC(14, 2) DEFAULT 0.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminder_logs_case 
ON debt_reminder_logs(case_id, status);