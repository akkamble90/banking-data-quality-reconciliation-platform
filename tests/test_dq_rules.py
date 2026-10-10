import pytest
import pandas as pd

def test_duplicate_transaction_detection():
    # Test data with explicit duplicate
    data = [
        {"txn_id": "TXN_1", "amount": 100.0},
        {"txn_id": "TXN_1", "amount": 100.0},
        {"txn_id": "TXN_2", "amount": 250.0}
    ]
    df = pd.DataFrame(data)
    duplicates = df[df.duplicated(subset=["txn_id"], keep=False)]
    
    assert len(duplicates) == 2
    assert "TXN_1" in duplicates["txn_id"].values

def test_reconciliation_bucket_logic():
    core = pd.DataFrame([{"txn_id": "T1", "amount": 100.0}, {"txn_id": "T2", "amount": 200.0}])
    settlement = pd.DataFrame([{"txn_id": "T1", "amount": 100.0}, {"txn_id": "T2", "amount": 180.0}])
    
    merged = pd.merge(core, settlement, on="txn_id", suffixes=("_core", "_settle"))
    mismatches = merged[merged["amount_core"] != merged["amount_settle"]]
    
    assert len(mismatches) == 1
    assert mismatches.iloc[0]["txn_id"] == "T2"