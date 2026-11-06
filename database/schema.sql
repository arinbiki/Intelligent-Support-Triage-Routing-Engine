-- ==============================================================================
-- Schema: Support Triage & Audit Database
-- Engine: SQLite 3 with WAL Mode and Covering Indexes
-- ==============================================================================

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. Support Tickets Table
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    customer_tier TEXT NOT NULL DEFAULT 'Standard', -- 'VIP', 'Standard'
    channel TEXT NOT NULL DEFAULT 'email',           -- 'email', 'chat', 'web_form'
    customer_email_masked TEXT NOT NULL,
    sanitized_subject TEXT NOT NULL,
    sanitized_body TEXT NOT NULL,
    extracted_order_ids TEXT,                        -- JSON array
    extracted_tracking_numbers TEXT,                 -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Triage Decisions Audit Log (Zero-LLM Traceability)
CREATE TABLE IF NOT EXISTS triage_audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    predicted_department TEXT NOT NULL,             -- 'Billing', 'Fulfillment', 'Technical', 'General'
    confidence REAL NOT NULL,                       -- 0.0 to 1.0
    confidence_gated BOOLEAN NOT NULL,              -- 1 = Auto-Route, 0 = Suspend/Human Triage
    vader_compound REAL NOT NULL,
    vader_negative REAL NOT NULL,
    urgency_score INTEGER NOT NULL,                 -- 0 (Low), 1 (Normal), 2 (Elevated), 3 (Critical)
    kill_switch_triggered BOOLEAN NOT NULL,
    trigger_keywords TEXT,                          -- JSON array
    refund_intent_detected BOOLEAN NOT NULL,
    refund_order_id TEXT,
    return_eligible BOOLEAN,
    final_assigned_queue TEXT NOT NULL,
    applied_tags TEXT NOT NULL,                     -- JSON array
    sla_minutes INTEGER NOT NULL,
    human_review_required BOOLEAN NOT NULL DEFAULT 0,
    dag_execution_latency_ms REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
);

CREATE INDEX IF NOT EXISTS idx_triage_audit_ticket ON triage_audit_log (ticket_id);
CREATE INDEX IF NOT EXISTS idx_triage_audit_department ON triage_audit_log (predicted_department);
CREATE INDEX IF NOT EXISTS idx_triage_audit_urgency ON triage_audit_log (urgency_score);

-- 3. Mock ERP Orders Table (For Return Eligibility Verification)
CREATE TABLE IF NOT EXISTS orders_erp (
    order_id TEXT PRIMARY KEY,                       -- e.g. '#84920'
    customer_id TEXT NOT NULL,
    customer_tier TEXT NOT NULL DEFAULT 'Standard',
    purchase_date TIMESTAMP NOT NULL,
    fulfillment_date TIMESTAMP,
    order_status TEXT NOT NULL,                     -- 'DELIVERED', 'SHIPPED', 'PROCESSING', 'CANCELLED'
    total_amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    is_final_sale BOOLEAN NOT NULL DEFAULT 0,       -- Clearance items cannot be returned
    items_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders_erp (customer_id);

-- 4. Shadow Evaluation Table (For 14-day calibration)
CREATE TABLE IF NOT EXISTS shadow_evaluations (
    eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    agent_decision_department TEXT NOT NULL,
    human_agent_department TEXT,
    agent_confidence REAL NOT NULL,
    is_match BOOLEAN,
    reviewed_by_human BOOLEAN NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
