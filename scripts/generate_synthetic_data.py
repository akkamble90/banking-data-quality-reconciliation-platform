import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Set seed for reproducible anomaly generation
random.seed(42)
np.random.seed(42)

DATA_RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(DATA_RAW_DIR, exist_ok=True)

def generate_banking_data(num_customers=500, num_accounts=800, num_txns=5000):
    batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 1. Customers
    cust_ids = [f"CUST_{1000 + i}" for i in range(num_customers)]
    regions = ["NORTH_AMERICA", "LATAM", "EMEA", "APAC"]
    kyc_statuses = ["VERIFIED", "VERIFIED", "VERIFIED", "PENDING", "EXPIRED"]
    
    customers = []
    for cid in cust_ids:
        customers.append({
            "raw_customer_id": cid,
            "full_name": f"Customer {cid.split('_')[1]}",
            "dob": (datetime(1970, 1, 1) + timedelta(days=random.randint(0, 12000))).strftime("%Y-%m-%d"),
            "kyc_status": random.choice(kyc_statuses),
            "region": random.choice(regions),
            "batch_id": batch_id
        })
    
    # Inject NULL customer names (Data Quality defect)
    for i in range(0, 15):
        customers[i]["full_name"] = None

    # 2. Accounts
    acc_ids = [f"ACC_{5000 + i}" for i in range(num_accounts)]
    acc_types = ["CHECKING", "SAVINGS", "CREDIT", "INVESTMENT"]
    acc_statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "DORMANT", "FROZEN"]
    
    accounts = []
    for aid in acc_ids:
        accounts.append({
            "raw_account_id": aid,
            "raw_customer_id": random.choice(cust_ids),
            "account_type": random.choice(acc_types),
            "balance": round(random.uniform(100.0, 50000.0), 2),
            "status": random.choice(acc_statuses),
            "batch_id": batch_id
        })
        
    # 3. Core Transactions
    txn_types = ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT"]
    channels = ["MOBILE", "WEB", "ATM", "BRANCH"]
    base_date = datetime.now() - timedelta(days=1)
    
    transactions = []
    for i in range(num_txns):
        tid = f"TXN_{100000 + i}"
        transactions.append({
            "raw_txn_id": tid,
            "raw_account_id": random.choice(acc_ids),
            "txn_date": (base_date + timedelta(seconds=random.randint(0, 86400))).strftime("%Y-%m-%d %H:%M:%S"),
            "txn_amount": round(random.uniform(5.0, 3000.0), 2),
            "txn_type": random.choice(txn_types),
            "channel": random.choice(channels),
            "batch_id": batch_id
        })
        
    # Inject Duplicate Transactions
    for i in range(20):
        dup = transactions[i].copy()
        dup["txn_amount"] = round(dup["txn_amount"] + random.uniform(1.0, 10.0), 2)
        transactions.append(dup)
        
    # Inject Orphan Transactions (referencing missing accounts)
    for i in range(15):
        transactions.append({
            "raw_txn_id": f"TXN_ORPHAN_{i}",
            "raw_account_id": "ACC_INVALID_9999",
            "txn_date": base_date.strftime("%Y-%m-%d %H:%M:%S"),
            "txn_amount": 150.00,
            "txn_type": "PAYMENT",
            "channel": "WEB",
            "batch_id": batch_id
        })

    # 4. Settlement Feed
    settlement = []
    for txn in transactions:
        roll = random.random()
        if roll < 0.95:
            # Matched
            settlement.append({
                "raw_txn_id": txn["raw_txn_id"],
                "settlement_date": txn["txn_date"],
                "settled_amount": txn["txn_amount"],
                "gateway_status": "SETTLED",
                "batch_id": batch_id
            })
        elif roll < 0.98:
            # Amount Mismatch
            settlement.append({
                "raw_txn_id": txn["raw_txn_id"],
                "settlement_date": txn["txn_date"],
                "settled_amount": round(txn["txn_amount"] * random.uniform(0.9, 1.1), 2),
                "gateway_status": "SETTLED",
                "batch_id": batch_id
            })
        # Remaining 2% skipped (Unmatched in Settlement)

    # Export to CSV files in data/raw
    pd.DataFrame(customers).to_csv(os.path.join(DATA_RAW_DIR, "raw_customers.csv"), index=False)
    pd.DataFrame(accounts).to_csv(os.path.join(DATA_RAW_DIR, "raw_accounts.csv"), index=False)
    pd.DataFrame(transactions).to_csv(os.path.join(DATA_RAW_DIR, "raw_transactions.csv"), index=False)
    pd.DataFrame(settlement).to_csv(os.path.join(DATA_RAW_DIR, "raw_settlement.csv"), index=False)

    print(f"[{batch_id}] Generated raw synthetic banking CSVs in 'data/raw/' successfully.")

if __name__ == "__main__":
    generate_banking_data()