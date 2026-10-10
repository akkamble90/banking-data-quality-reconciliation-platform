import os
import sys
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

# Build dynamic database connection URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Resolve path to raw data directory
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

def ingest_raw_files():
    print(f"=== Database Ingestion Started ===")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_RAW_DIR}")
    
    if not os.path.exists(DATA_RAW_DIR):
        print(f"ERROR: Directory '{DATA_RAW_DIR}' does not exist!")
        sys.exit(1)

    # Validate that required environment variables are loaded
    if not all([DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME]):
        print("ERROR: Database credentials missing. Ensure .env file is properly configured.")
        sys.exit(1)

    try:
        engine = create_engine(DATABASE_URL)
        with engine.begin() as connection:
            print(f"Successfully connected to PostgreSQL database ({DB_NAME}).")
            
            files_map = {
                "raw_customers.csv": ("staging", "stg_customers"),
                "raw_accounts.csv": ("staging", "stg_accounts"),
                "raw_transactions.csv": ("staging", "stg_transactions"),
                "raw_settlement.csv": ("staging", "stg_settlement")
            }

            for file_name, (schema, table) in files_map.items():
                file_path = os.path.join(DATA_RAW_DIR, file_name)
                
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    
                    # Clear staging table before loading new batch
                    connection.execute(text(f"TRUNCATE TABLE {schema}.{table};"))
                    
                    # Append DataFrame records to PostgreSQL staging table
                    df.to_sql(name=table, schema=schema, con=connection, if_exists="append", index=False)
                    print(f"SUCCESS: Ingested {len(df)} records into {schema}.{table}")
                else:
                    print(f"WARNING: File '{file_path}' was not found.")

    except Exception as e:
        print(f"DATABASE ERROR: {e}")

if __name__ == "__main__":
    ingest_raw_files()