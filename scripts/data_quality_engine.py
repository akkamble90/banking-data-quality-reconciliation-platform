import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables from .env file located in project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Read ALL database parameters strictly from environment variables
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def run_data_quality_checks():
    """Executes automated reconciliation queries and prints exception summaries."""
    try:
        # Check if required environment variables are set
        if not DB_CONFIG["password"] or not DB_CONFIG["dbname"]:
            raise ValueError("Database credentials missing. Ensure .env file is populated.")

        conn = psycopg2.connect(**DB_CONFIG)
        print(f"Connected to PostgreSQL database ({DB_CONFIG['dbname']}) successfully.")

        # 1. Query Settlement Lag & Financial Exposure Summary
        df_lag = pd.read_sql("SELECT * FROM audit.v_settlement_lag_variance;", conn)
        print("\n--- Settlement Lag & Financial Exposure Summary ---")
        print(df_lag[['channel', 'total_settled_txns', 'net_unreconciled_variance', 'avg_settlement_lag_minutes']])

        # 2. Query High Severity Governance Alerts
        df_alerts = pd.read_sql("SELECT * FROM audit.v_governance_alerts WHERE severity = 'HIGH';", conn)
        print(f"\n[GOVERNANCE ALERT] Detected {len(df_alerts)} high-severity data quality violations.")

        conn.close()
    except Exception as e:
        print(f"Error executing Data Quality Engine: {e}")

if __name__ == "__main__":
    run_data_quality_checks()