-- ============================================================================
-- SQL RECONCILIATION ENGINE
-- Compares Core Transactions against Gateway Settlement Feed
-- ============================================================================

-- 1. Detailed Record-Level Reconciliation Join
WITH recon_base AS (
    SELECT 
        COALESCE(t.raw_txn_id, s.raw_txn_id) AS txn_id,
        t.raw_account_id,
        t.txn_amount AS core_amount,
        s.settled_amount AS settlement_amount,
        t.txn_date AS core_txn_date,
        s.settlement_date,
        s.gateway_status,
        CASE 
            WHEN t.raw_txn_id IS NULL THEN 'UNMATCHED_SETTLEMENT'
            WHEN s.raw_txn_id IS NULL THEN 'UNMATCHED_CORE'
            WHEN t.txn_amount <> s.settled_amount THEN 'AMOUNT_MISMATCH'
            ELSE 'MATCHED'
        END AS recon_status,
        ABS(COALESCE(t.txn_amount, 0) - COALESCE(s.settled_amount, 0)) AS variance_amount
    FROM staging.stg_transactions t
    FULL OUTER JOIN staging.stg_settlement s 
        ON t.raw_txn_id = s.raw_txn_id
)
SELECT * 
FROM recon_base
ORDER BY recon_status DESC, variance_amount DESC;

-- 2. Executive Daily Reconciliation Summary Aggregation
WITH recon_categorized AS (
    SELECT 
        COALESCE(t.raw_txn_id, s.raw_txn_id) AS txn_id,
        t.txn_amount AS core_amount,
        s.settled_amount AS settlement_amount,
        CASE 
            WHEN t.raw_txn_id IS NULL THEN 'UNMATCHED_SETTLEMENT'
            WHEN s.raw_txn_id IS NULL THEN 'UNMATCHED_CORE'
            WHEN t.txn_amount <> s.settled_amount THEN 'AMOUNT_MISMATCH'
            ELSE 'MATCHED'
        END AS recon_status,
        ABS(COALESCE(t.txn_amount, 0) - COALESCE(s.settled_amount, 0)) AS variance_amount
    FROM staging.stg_transactions t
    FULL OUTER JOIN staging.stg_settlement s 
        ON t.raw_txn_id = s.raw_txn_id
)
SELECT 
    CURRENT_DATE AS recon_date,
    COUNT(CASE WHEN recon_status <> 'UNMATCHED_SETTLEMENT' THEN 1 END) AS total_core_records,
    COUNT(CASE WHEN recon_status <> 'UNMATCHED_CORE' THEN 1 END) AS total_settlement_records,
    COUNT(CASE WHEN recon_status = 'MATCHED' THEN 1 END) AS matched_count,
    COUNT(CASE WHEN recon_status = 'UNMATCHED_CORE' THEN 1 END) AS unmatched_core_count,
    COUNT(CASE WHEN recon_status = 'UNMATCHED_SETTLEMENT' THEN 1 END) AS unmatched_settlement_count,
    COUNT(CASE WHEN recon_status = 'AMOUNT_MISMATCH' THEN 1 END) AS amount_mismatch_count,
    SUM(variance_amount) AS total_variance_amount,
    ROUND(
        (COUNT(CASE WHEN recon_status = 'MATCHED' THEN 1 END)::NUMERIC / 
         NULLIF(COUNT(CASE WHEN recon_status <> 'UNMATCHED_SETTLEMENT' THEN 1 END), 0)) * 100, 2
    ) AS match_rate_pct
FROM recon_categorized;