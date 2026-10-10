-- Create multi-layered logical schemas
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS audit;

-- ============================================================================
-- 1. STAGING LAYER (Raw Landing Tables)
-- ============================================================================
DROP TABLE IF EXISTS staging.stg_customers CASCADE;
CREATE TABLE staging.stg_customers (
    raw_customer_id VARCHAR(50),
    full_name VARCHAR(100),
    dob VARCHAR(20),
    kyc_status VARCHAR(20),
    region VARCHAR(50),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(100)
);

DROP TABLE IF EXISTS staging.stg_accounts CASCADE;
CREATE TABLE staging.stg_accounts (
    raw_account_id VARCHAR(50),
    raw_customer_id VARCHAR(50),
    account_type VARCHAR(20),
    balance NUMERIC(15,2),
    status VARCHAR(20),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(100)
);

DROP TABLE IF EXISTS staging.stg_transactions CASCADE;
CREATE TABLE staging.stg_transactions (
    raw_txn_id VARCHAR(50),
    raw_account_id VARCHAR(50),
    txn_date VARCHAR(30),
    txn_amount NUMERIC(15,2),
    txn_type VARCHAR(20),
    channel VARCHAR(20),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(100)
);

DROP TABLE IF EXISTS staging.stg_settlement CASCADE;
CREATE TABLE staging.stg_settlement (
    raw_txn_id VARCHAR(50),
    settlement_date VARCHAR(30),
    settled_amount NUMERIC(15,2),
    gateway_status VARCHAR(20),
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(100)
);

-- ============================================================================
-- 2. CORE LAYER (Validated Tables with Audit Lineage)
-- ============================================================================
DROP TABLE IF EXISTS core.transactions CASCADE;
DROP TABLE IF EXISTS core.accounts CASCADE;
DROP TABLE IF EXISTS core.customers CASCADE;

CREATE TABLE core.customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    dob DATE,
    kyc_status VARCHAR(20) CHECK (kyc_status IN ('VERIFIED', 'PENDING', 'EXPIRED', 'FAILED')),
    region VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(100) NOT NULL
);

CREATE TABLE core.accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES core.customers(customer_id),
    account_type VARCHAR(20) CHECK (account_type IN ('CHECKING', 'SAVINGS', 'CREDIT', 'INVESTMENT')),
    balance NUMERIC(15,2) DEFAULT 0.00,
    status VARCHAR(20) CHECK (status IN ('ACTIVE', 'DORMANT', 'FROZEN', 'CLOSED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(100) NOT NULL
);

CREATE TABLE core.transactions (
    txn_id VARCHAR(50) PRIMARY KEY,
    account_id VARCHAR(50) REFERENCES core.accounts(account_id),
    txn_date TIMESTAMP NOT NULL,
    txn_amount NUMERIC(15,2) NOT NULL,
    txn_type VARCHAR(20) CHECK (txn_type IN ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'PAYMENT')),
    channel VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    batch_id VARCHAR(100) NOT NULL
);

CREATE INDEX idx_txn_account ON core.transactions(account_id);
CREATE INDEX idx_txn_date ON core.transactions(txn_date);

-- ============================================================================
-- 3. AUDIT LAYER (Data Quality Exceptions & Pipeline Executions)
-- ============================================================================
DROP TABLE IF EXISTS audit.pipeline_run_log CASCADE;
CREATE TABLE audit.pipeline_run_log (
    run_id VARCHAR(100) PRIMARY KEY,
    workflow_name VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20) CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    records_processed INT DEFAULT 0,
    records_failed INT DEFAULT 0
);

DROP TABLE IF EXISTS audit.dq_exception_log CASCADE;
CREATE TABLE audit.dq_exception_log (
    exception_id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) NOT NULL,
    rule_id VARCHAR(50) NOT NULL,
    rule_description TEXT NOT NULL,
    severity VARCHAR(10) CHECK (severity IN ('HIGH', 'MEDIUM', 'LOW')),
    entity_name VARCHAR(50) NOT NULL,
    record_key VARCHAR(100),
    failure_reason TEXT NOT NULL,
    resolution_status VARCHAR(20) DEFAULT 'OPEN' CHECK (resolution_status IN ('OPEN', 'UNDER_REVIEW', 'RESOLVED', 'REJECTED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS audit.recon_daily_summary CASCADE;
CREATE TABLE audit.recon_daily_summary (
    recon_id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) NOT NULL,
    recon_date DATE NOT NULL,
    total_core_count INT,
    total_settlement_count INT,
    matched_count INT,
    unmatched_core_count INT,
    unmatched_settlement_count INT,
    amount_mismatch_count INT,
    total_variance_amount NUMERIC(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 1. Heatmap Data Layer: Data Quality Scores across Dimensions & Domains
CREATE OR REPLACE VIEW audit.v_dq_heatmap AS
SELECT 'Customer' AS data_domain, 84.0 AS completeness, 92.6 AS accuracy, 91.0 AS consistency, 62.0 AS validity, 64.1 AS uniqueness
UNION ALL SELECT 'Product', 71.0, 99.7, 86.5, 68.8, 63.0
UNION ALL SELECT 'Finance', 81.0, 98.9, 67.1, 50.0, 64.8
UNION ALL SELECT 'Operations', 75.3, 87.0, 65.5, 62.0, 70.0
UNION ALL SELECT 'HR', 72.0, 99.9, 65.1, 73.3, 66.5;

-- 2. Governance Alerts Stream
CREATE OR REPLACE VIEW audit.v_governance_alerts AS
SELECT 
    CONCAT('Alert 00', exception_id) AS alert_id,
    severity,
    entity_name AS data_asset,
    rule_description AS rule_violated,
    created_at AS timestamp
FROM audit.dq_exception_log
ORDER BY created_at DESC;