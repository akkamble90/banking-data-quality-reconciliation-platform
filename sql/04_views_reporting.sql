-- ============================================================================
-- OPERATIONAL REPORTING VIEWS
-- ============================================================================

-- View 1: Daily Exception Operational Queue
CREATE OR REPLACE VIEW audit.v_open_exceptions_queue AS
SELECT 
    exception_id,
    run_id,
    rule_id,
    rule_description,
    severity,
    entity_name,
    record_key,
    failure_reason,
    resolution_status,
    created_at
FROM audit.dq_exception_log
WHERE resolution_status IN ('OPEN', 'UNDER_REVIEW')
ORDER BY 
    CASE severity 
        WHEN 'HIGH' THEN 1 
        WHEN 'MEDIUM' THEN 2 
        WHEN 'LOW' THEN 3 
    END, created_at DESC;

-- View 2: Executive Reconciliation Performance Metrics
CREATE OR REPLACE VIEW audit.v_recon_executive_kpis AS
SELECT 
    run_id,
    recon_date,
    total_core_count,
    total_settlement_count,
    matched_count,
    unmatched_core_count,
    unmatched_settlement_count,
    amount_mismatch_count,
    total_variance_amount,
    ROUND((matched_count::NUMERIC / NULLIF(total_core_count, 0)) * 100, 2) AS match_rate_pct
FROM audit.recon_daily_summary;
-- 1. Statistical Transaction Velocity & Anomaly Risk Score (Z-Score Model)
CREATE OR REPLACE VIEW audit.v_transaction_anomaly_analytics AS
WITH channel_stats AS (
    SELECT 
        channel,
        AVG(txn_amount) AS avg_amount,
        STDDEV(txn_amount) AS stddev_amount,
        COUNT(*) AS total_volume
    FROM core.transactions
    GROUP BY channel
)
SELECT 
    t.txn_id,
    t.account_id,
    t.channel,
    t.txn_amount,
    cs.avg_amount,
    -- Statistical Z-score calculation to isolate extreme transaction outliers (> 2.0 Sigma)
    ROUND(
        (t.txn_amount - cs.avg_amount) / NULLIF(cs.stddev_amount, 0), 2
    ) AS z_score_risk,
    CASE 
        WHEN ABS((t.txn_amount - cs.avg_amount) / NULLIF(cs.stddev_amount, 0)) >= 3.0 THEN 'CRITICAL_ANOMALY'
        WHEN ABS((t.txn_amount - cs.avg_amount) / NULLIF(cs.stddev_amount, 0)) >= 2.0 THEN 'ELEVATED_RISK'
        ELSE 'NORMAL_RANGE'
    END AS risk_tier,
    t.txn_date
FROM core.transactions t
JOIN channel_stats cs ON t.channel = cs.channel;


-- 2. Multi-Leg Settlement Variance & Gateway Lag Analysis
CREATE OR REPLACE VIEW audit.v_settlement_lag_variance AS
SELECT 
    t.channel,
    t.txn_type,
    s.gateway_status,
    COUNT(t.txn_id) AS total_settled_txns,
    SUM(t.txn_amount) AS gross_core_volume,
    SUM(s.settled_amount) AS gross_settled_volume,
    SUM(ABS(t.txn_amount - s.settled_amount)) AS net_unreconciled_variance,
    -- Quantifies settlement timing delay in minutes
    ROUND(
        AVG(EXTRACT(EPOCH FROM (s.settlement_date::timestamp - t.txn_date::timestamp)) / 60.0), 2
    ) AS avg_settlement_lag_minutes
FROM core.transactions t
JOIN staging.stg_settlement s ON t.txn_id = s.raw_txn_id
GROUP BY t.channel, t.txn_type, s.gateway_status;