#!/bin/bash

# Pipeline Orchestration Script
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR="../data/logs"
LOG_FILE="${LOG_DIR}/pipeline_${TIMESTAMP}.log"

mkdir -p "${LOG_DIR}"

echo "==========================================================" | tee -a "${LOG_FILE}"
echo "  CITI DATA QUALITY & RECONCILIATION PIPELINE STARTED     " | tee -a "${LOG_FILE}"
echo "  Timestamp: ${TIMESTAMP}                                " | tee -a "${LOG_FILE}"
echo "==========================================================" | tee -a "${LOG_FILE}"

# Step 1: Generate Synthetic Data
echo "[1/3] Generating Synthetic Banking Data..." | tee -a "${LOG_FILE}"
python3 generate_synthetic_data.py >> "${LOG_FILE}" 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Data generation failed! Check log file." | tee -a "${LOG_FILE}"
    exit 1
fi

# Step 2: Ingest Data to PostgreSQL Staging
echo "[2/3] Ingesting CSVs to PostgreSQL Staging Layer..." | tee -a "${LOG_FILE}"
python3 db_ingestion.py >> "${LOG_FILE}" 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Database ingestion failed!" | tee -a "${LOG_FILE}"
    exit 1
fi

# Step 3: Run PySpark Reconciliation Engine
echo "[3/3] Running PySpark Data Quality & Reconciliation Engine..." | tee -a "${LOG_FILE}"
python3 dq_engine_pyspark.py >> "${LOG_FILE}" 2>&1

echo "==========================================================" | tee -a "${LOG_FILE}"
echo "  PIPELINE EXECUTION COMPLETED SUCCESSFULLY AT $(date)    " | tee -a "${LOG_FILE}"
echo "==========================================================" | tee -a "${LOG_FILE}"