import os
import sys
from datetime import datetime
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from sqlalchemy import create_engine
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

# Build dynamic database connection URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def run_pyspark_reconciliation():
    run_id = f"RUN_SPARK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"=== Starting PySpark Data Quality & Reconciliation Engine [{run_id}] ===")

    # Initialize PySpark Session
    spark = SparkSession.builder \
        .appName("CitiBankingReconciliationEngine") \
        .config("spark.driver.extraClassPath", "postgresql-42.6.0.jar") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    try:
        # Read staging tables via SQLAlchemy / Pandas bridge
        engine = create_engine(DATABASE_URL)
        
        pdf_txns = pd.read_sql("SELECT * FROM staging.stg_transactions", engine)
        pdf_settlement = pd.read_sql("SELECT * FROM staging.stg_settlement", engine)

        df_txns = spark.createDataFrame(pdf_txns)
        df_settlement = spark.createDataFrame(pdf_settlement)

        print(f"Loaded {df_txns.count()} Core Transactions and {df_settlement.count()} Settlement Records.")

        # 1. Reconciliation Outer Join
        recon_df = df_txns.alias("t").join(
            df_settlement.alias("s"),
            F.col("t.raw_txn_id") == F.col("s.raw_txn_id"),
            "full_outer"
        ).select(
            F.coalesce(F.col("t.raw_txn_id"), F.col("s.raw_txn_id")).alias("txn_id"),
            F.col("t.txn_amount").alias("core_amount"),
            F.col("s.settled_amount").alias("settlement_amount"),
            F.when(F.col("t.raw_txn_id").isNull(), "UNMATCHED_SETTLEMENT")
             .when(F.col("s.raw_txn_id").isNull(), "UNMATCHED_CORE")
             .when(F.col("t.txn_amount") != F.col("s.settled_amount"), "AMOUNT_MISMATCH")
             .otherwise("MATCHED").alias("recon_status"),
            F.abs(F.coalesce(F.col("t.txn_amount"), F.lit(0)) - F.coalesce(F.col("s.settled_amount"), F.lit(0))).alias("variance_amount")
        )

        # Calculate Aggregates
        summary_counts = recon_df.groupBy("recon_status").count().collect()
        counts_dict = {row["recon_status"]: row["count"] for row in summary_counts}

        matched_cnt = counts_dict.get("MATCHED", 0)
        unmatched_core_cnt = counts_dict.get("UNMATCHED_CORE", 0)
        unmatched_settlement_cnt = counts_dict.get("UNMATCHED_SETTLEMENT", 0)
        amount_mismatch_cnt = counts_dict.get("AMOUNT_MISMATCH", 0)
        
        total_variance = recon_df.groupBy().agg(F.sum("variance_amount")).collect()[0][0] or 0.0

        print(f"\n--- RECONCILIATION SUMMARY ---")
        print(f"Matched Records: {matched_cnt}")
        print(f"Unmatched Core Transactions: {unmatched_core_cnt}")
        print(f"Unmatched Settlement Records: {unmatched_settlement_cnt}")
        print(f"Amount Mismatches: {amount_mismatch_cnt}")
        print(f"Total Variance Amount: ${total_variance:,.2f}")

        # Write Reconciliation Audit Summary back to PostgreSQL
        recon_summary_pdf = pd.DataFrame([{
            "run_id": run_id,
            "recon_date": datetime.now().strftime("%Y-%m-%d"),
            "total_core_count": df_txns.count(),
            "total_settlement_count": df_settlement.count(),
            "matched_count": matched_cnt,
            "unmatched_core_count": unmatched_core_cnt,
            "unmatched_settlement_count": unmatched_settlement_cnt,
            "amount_mismatch_count": amount_mismatch_cnt,
            "total_variance_amount": round(total_variance, 2),
            "created_at": datetime.now()
        }])

        recon_summary_pdf.to_sql("recon_daily_summary", schema="audit", con=engine, if_exists="append", index=False)
        print("Reconciliation summary successfully recorded in 'audit.recon_daily_summary'.")

    except Exception as e:
        print(f"PYSPARK ENGINE ERROR: {e}")
    finally:
        spark.stop()

if __name__ == "__main__":
    run_pyspark_reconciliation()