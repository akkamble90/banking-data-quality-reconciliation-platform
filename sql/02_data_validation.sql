-- ============================================================================
-- SQL DATA QUALITY VALIDATION ENGINE
-- Identifies duplicate keys, referential integrity breaks, and missing values
-- ============================================================================

-- Rule DQ_001: Duplicate Transaction Key Detection
SELECT 
    raw_txn_id,
    raw_account_id,
    txn_amount,
    COUNT(*) AS occurrence_count
FROM staging.stg_transactions
GROUP BY raw_txn_id, raw_account_id, txn_amount
HAVING COUNT(*) > 1;

-- Rule DQ_002: Referential Integrity (Orphan Transactions without valid Account)
SELECT 
    t.raw_txn_id,
    t.raw_account_id,
    t.txn_amount,
    'ORPHAN_ACCOUNT_FK' AS failure_reason
FROM staging.stg_transactions t
LEFT JOIN staging.stg_accounts a ON t.raw_account_id = a.raw_account_id
WHERE a.raw_account_id IS NULL;

-- Rule DQ_003: Mandatory Field Check (Missing Customer Name)
SELECT 
    raw_customer_id,
    region,
    kyc_status,
    'NULL_CUSTOMER_NAME' AS failure_reason
FROM staging.stg_customers
WHERE full_name IS NULL OR TRIM(full_name) = '';