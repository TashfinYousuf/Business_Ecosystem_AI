-- backend/database/migrations/003_agent_runtime.sql
-- Durable Agent Workflow State Machine & Human Approval Gate Schema

-- 1. Agent Workflow Run Executions (State Snapshots)
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    workflow_name VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'RUNNING' 
        CHECK(status IN ('RUNNING', 'SUSPENDED_AWAITING_APPROVAL', 'RESUMED', 'COMPLETED', 'FAILED', 'REJECTED')),
    current_step INT NOT NULL DEFAULT 1,
    state_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_executions_org_status 
ON agent_executions(org_id, status);

-- 2. Human Approval Gate Queue (Pending Merchant/Admin Confirmations)
CREATE TABLE IF NOT EXISTS agent_approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES agent_executions(id) ON DELETE CASCADE,
    org_id UUID NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    action_summary TEXT NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk_level VARCHAR(16) NOT NULL DEFAULT 'MEDIUM' CHECK(risk_level IN ('LOW', 'MEDIUM', 'CRITICAL')),
    status VARCHAR(16) NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID,
    resolution_note TEXT
);

CREATE INDEX IF NOT EXISTS idx_agent_approvals_org_pending 
ON agent_approval_requests(org_id, status);