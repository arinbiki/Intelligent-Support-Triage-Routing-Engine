import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "triage_audit.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")

def init_database():
    print(f"[*] Initializing database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Execute schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    # Check if orders already populated
    cursor.execute("SELECT COUNT(*) FROM orders_erp")
    count = cursor.fetchone()[0]

    if count == 0:
        print("[*] Seeding mock ERP orders for return eligibility engine...")
        now = datetime.utcnow()
        sample_orders = [
            (
                "#84920",
                "CUST-001",
                "VIP",
                (now - timedelta(days=3)).isoformat(),
                (now - timedelta(days=1)).isoformat(),
                "DELIVERED",
                189.99,
                "USD",
                0,
                json.dumps([{"sku": "ANC-PRO-HEADPHONES", "qty": 1, "price": 189.99}])
            ),
            (
                "#1001",
                "CUST-002",
                "Standard",
                (now - timedelta(days=5)).isoformat(),
                (now - timedelta(days=2)).isoformat(),
                "DELIVERED",
                149.99,
                "USD",
                0,
                json.dumps([{"sku": "MECHANICAL-KB", "qty": 1, "price": 149.99}])
            ),
            (
                "#1002",
                "CUST-003",
                "Standard",
                (now - timedelta(days=45)).isoformat(),
                (now - timedelta(days=40)).isoformat(),
                "DELIVERED",
                89.50,
                "USD",
                0,
                json.dumps([{"sku": "GAMING-MOUSE", "qty": 1, "price": 89.50}])
            ),
            (
                "#1003",
                "CUST-004",
                "Standard",
                (now - timedelta(days=10)).isoformat(),
                (now - timedelta(days=7)).isoformat(),
                "DELIVERED",
                299.00,
                "USD",
                1, # Final sale / Clearance
                json.dumps([{"sku": "CLEARANCE-MONITOR", "qty": 1, "price": 299.00}])
            ),
            (
                "#1004",
                "CUST-005",
                "VIP",
                (now - timedelta(days=2)).isoformat(),
                None,
                "PROCESSING",
                450.00,
                "USD",
                0,
                json.dumps([{"sku": "ERGONOMIC-CHAIR", "qty": 1, "price": 450.00}])
            ),
            (
                "#9999",
                "CUST-006",
                "Standard",
                (now - timedelta(days=12)).isoformat(),
                (now - timedelta(days=9)).isoformat(),
                "DELIVERED",
                65.00,
                "USD",
                0,
                json.dumps([{"sku": "DESK-MAT", "qty": 2, "price": 32.50}])
            )
        ]

        cursor.executemany("""
            INSERT INTO orders_erp 
            (order_id, customer_id, customer_tier, purchase_date, fulfillment_date, order_status, total_amount, currency, is_final_sale, items_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_orders)

        # Seed 100 additional realistic orders
        additional_orders = []
        for i in range(1005, 1150):
            days_ago = (i * 7) % 50 + 1
            purchased = now - timedelta(days=days_ago)
            fulfilled = purchased + timedelta(days=2) if days_ago >= 2 else None
            status = "DELIVERED" if fulfilled else "PROCESSING"
            final_sale = 1 if i % 17 == 0 else 0
            tier = "VIP" if i % 10 == 0 else "Standard"
            amt = round(35.0 + (i % 25) * 15.5, 2)
            additional_orders.append((
                f"#{i}",
                f"CUST-{i}",
                tier,
                purchased.isoformat(),
                fulfilled.isoformat() if fulfilled else None,
                status,
                amt,
                "USD",
                final_sale,
                json.dumps([{"sku": f"SKU-{i%20}", "qty": 1, "price": amt}])
            ))

        cursor.executemany("""
            INSERT INTO orders_erp 
            (order_id, customer_id, customer_tier, purchase_date, fulfillment_date, order_status, total_amount, currency, is_final_sale, items_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, additional_orders)

        conn.commit()
        print(f"[+] Successfully seeded {len(sample_orders) + len(additional_orders)} orders into orders_erp.")
    else:
        print(f"[i] orders_erp already contains {count} records.")

    conn.close()
    print("[+] Database initialization complete.")

if __name__ == "__main__":
    init_database()

