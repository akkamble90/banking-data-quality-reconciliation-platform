# Data Quality Rules Matrix & Controls

| Rule ID | Rule Description | Entity Checked | Condition / Logic | Severity | Action on Failure |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DQ_001** | Duplicate Transaction Detection | `stg_transactions` | `COUNT(raw_txn_id) > 1` | **HIGH** | Quarantine record; log to exception queue. Prevent load to core. |
| **DQ_002** | Account Referential Integrity | `stg_transactions` | `raw_account_id NOT IN (core.accounts)` | **HIGH** | Flag as orphan transaction; require L2 Data Ops investigation. |
| **DQ_003** | Mandatory Customer Name | `stg_customers` | `full_name IS NULL OR TRIM(full_name) = ''` | **MEDIUM** | Log exception; route to KYC remediation team. |
| **DQ_004** | Frozen Account Activity | `stg_transactions` | `account.status IN ('FROZEN', 'CLOSED')` | **HIGH** | Trigger compliance review alert immediately. |
| **RECON_01** | Amount Matching Variance | `core.transactions` vs `stg_settlement` | `abs(txn_amount - settled_amount) > $0.00` | **MEDIUM** | Highlight in daily reconciliation summary and Power BI dashboard. |