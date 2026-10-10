# Enterprise Banking Data Dictionary

## 1. Staging Layer (`staging`)
Raw, unvalidated landing data ingested from operational CSV extracts.

### `staging.stg_customers`
| Field Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `raw_customer_id` | VARCHAR(50) | NO | Primary business identifier for customer |
| `full_name` | VARCHAR(100) | YES | Full legal name of customer |
| `dob` | VARCHAR(20) | YES | Date of birth (string format YYYY-MM-DD) |
| `kyc_status` | VARCHAR(20) | YES | Know-Your-Customer verification status |
| `region` | VARCHAR(50) | YES | Geographic operating region |
| `ingestion_timestamp` | TIMESTAMP | NO | System timestamp when record was staged |
| `batch_id` | VARCHAR(100) | NO | Unique batch execution identifier |

### `staging.stg_transactions`
| Field Name | Data Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `raw_txn_id` | VARCHAR(50) | NO | Transaction reference identifier |
| `raw_account_id` | VARCHAR(50) | NO | Associated account reference |
| `txn_date` | VARCHAR(30) | NO | Transaction timestamp string |
| `txn_amount` | NUMERIC(15,2) | NO | Monetary value of transaction |
| `txn_type` | VARCHAR(20) | YES | Category (DEPOSIT, WITHDRAWAL, TRANSFER, PAYMENT) |
| `channel` | VARCHAR(20) | YES | Channel (MOBILE, WEB, ATM, BRANCH) |
| `batch_id` | VARCHAR(100) | NO | Ingestion batch reference |

---

## 2. Core Layer (`core`)
Validated, production-ready relational tables with relational constraints and keys.

### `core.transactions`
| Field Name | Data Type | Key Type | Check Constraints / Description |
| :--- | :--- | :--- | :--- |
| `txn_id` | VARCHAR(50) | Primary Key | Unique transaction key |
| `account_id` | VARCHAR(50) | Foreign Key | References `core.accounts(account_id)` |
| `txn_date` | TIMESTAMP | - | Standardized transaction timestamp |
| `txn_amount` | NUMERIC(15,2) | - | Must be non-null monetary amount |
| `txn_type` | VARCHAR(20) | Check | Allowed: DEPOSIT, WITHDRAWAL, TRANSFER, PAYMENT |
| `channel` | VARCHAR(20) | - | Origin channel |
| `created_at` | TIMESTAMP | - | Record insertion timestamp |
| `batch_id` | VARCHAR(100) | - | Lineage batch reference |

---

## 3. Audit Layer (`audit`)
Data quality logs, exception queues, and financial reconciliation summaries.

### `audit.dq_exception_log`
| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `exception_id` | SERIAL (PK) | Auto-incrementing unique exception record ID |
| `run_id` | VARCHAR(100) | Associated execution workflow run ID |
| `rule_id` | VARCHAR(50) | Standardized DQ rule code (e.g., DQ_001) |
| `severity` | VARCHAR(10) | HIGH, MEDIUM, LOW |
| `entity_name` | VARCHAR(50) | Source table containing failure |
| `record_key` | VARCHAR(100) | Primary key of failed record |
| `failure_reason` | TEXT | Detailed failure message |
| `resolution_status` | VARCHAR(20) | OPEN, UNDER_REVIEW, RESOLVED, REJECTED |