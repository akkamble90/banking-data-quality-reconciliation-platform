import os
import sys
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Resolve absolute path to project root and load .env file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Read ALL database connection parameters strictly from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Validate that required environment variables are loaded
if not all([DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME]):
    print("ERROR: Database credentials missing. Ensure .env file is properly configured.")
    sys.exit(1)

# Build dynamic database connection URL and SQLAlchemy engine
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

def run_dq_checks():
    run_id = f"RUN_DQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"=== Running Data Quality Rules Engine [{run_id}] ===")
    
    exceptions = []

    try:
        # 1. Rule DQ_001: Duplicate Transactions Check
        df_txns = pd.read_sql("SELECT raw_txn_id, raw_account_id, txn_amount FROM staging.stg_transactions", engine)
        dups = df_txns[df_txns.duplicated(subset=["raw_txn_id"], keep=False)]
        for _, row in dups.iterrows():
            exceptions.append({
                "run_id": run_id,
                "rule_id": "DQ_001",
                "rule_description": "Duplicate Transaction Identifier",
                "severity": "HIGH",
                "entity_name": "stg_transactions",
                "record_key": str(row["raw_txn_id"]),
                "failure_reason": f"Transaction ID {row['raw_txn_id']} appears multiple times.",
                "resolution_status": "OPEN"
            })

        # 2. Rule DQ_002: Orphan Transactions (Missing Account Foreign Key)
        df_accs = pd.read_sql("SELECT raw_account_id FROM staging.stg_accounts", engine)
        valid_acc_ids = set(df_accs["raw_account_id"].dropna())
        orphans = df_txns[~df_txns["raw_account_id"].isin(valid_acc_ids)]
        for _, row in orphans.iterrows():
            exceptions.append({
                "run_id": run_id,
                "rule_id": "DQ_002",
                "rule_description": "Referential Integrity Failure - Missing Account",
                "severity": "HIGH",
                "entity_name": "stg_transactions",
                "record_key": str(row["raw_txn_id"]),
                "failure_reason": f"Account ID {row['raw_account_id']} does not exist in account core table.",
                "resolution_status": "OPEN"
            })

        # 3. Rule DQ_003: Mandatory Field Check (Missing Customer Name)
        df_custs = pd.read_sql("SELECT raw_customer_id, full_name FROM staging.stg_customers", engine)
        null_custs = df_custs[df_custs["full_name"].isna() | (df_custs["full_name"].str.strip() == "")]
        for _, row in null_custs.iterrows():
            exceptions.append({
                "run_id": run_id,
                "rule_id": "DQ_003",
                "rule_description": "Mandatory Attribute Null Check - Customer Name",
                "severity": "MEDIUM",
                "entity_name": "stg_customers",
                "record_key": str(row["raw_customer_id"]),
                "failure_reason": "Customer record missing required full_name attribute.",
                "resolution_status": "OPEN"
            })

        # Write exceptions to audit.dq_exception_log
        if exceptions:
            df_exc = pd.DataFrame(exceptions)
            df_exc.to_sql("dq_exception_log", schema="audit", con=engine, if_exists="append", index=False)
            print(f"SUCCESS: Logged {len(df_exc)} data quality exceptions into 'audit.dq_exception_log'.")
        else:
            print("No exceptions detected.")

    except Exception as e:
        print(f"DQ ENGINE ERROR: {e}")

if __name__ == "__main__":
    run_dq_checks()