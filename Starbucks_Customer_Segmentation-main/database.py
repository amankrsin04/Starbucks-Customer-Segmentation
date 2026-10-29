"""
database.py — Relational SQLite Database Layer
==============================================
Provides automated schema creation, indexing, and data seeding for:
- Customers (demographics, lifetime behavior, cluster assignments)
- Promotional Offers (catalog attributes, difficulty, reward, duration)
- Transcript Events (transactions, received, viewed, completed)
- Offer Performance & Aggregates
- Customer Pools
Zero manual setup required: automatically seeds from CSVs on startup if database is missing.
"""

import os
import json
import sqlite3
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "data", "starbucks_analytics.db")


def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_and_seed_database(data_dict, ml_cache, force_reseed=False):
    """
    Initializes database tables, creates indexes, and seeds data.
    """
    os.makedirs("data", exist_ok=True)
    db_exists = os.path.exists(DB_PATH)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if table already populated
    if db_exists and not force_reseed:
        try:
            cursor.execute("SELECT COUNT(*) FROM customers")
            count = cursor.fetchone()[0]
            if count > 0:
                logger.info(f"SQLite Database verified: {count} customer records already present.")
                conn.close()
                return
        except sqlite3.OperationalError:
            pass  # Table doesn't exist yet, proceed with creation

    logger.info("Initializing and seeding SQLite database...")

    # 1. Create Tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            gender TEXT,
            age INTEGER,
            income REAL,
            became_member_on TEXT,
            membership_days INTEGER,
            num_received INTEGER,
            num_viewed INTEGER,
            num_completed INTEGER,
            num_transactions INTEGER,
            money_spent REAL,
            view_rate REAL,
            completion_rate REAL,
            avg_transaction_amount REAL,
            cluster INTEGER,
            segment_name TEXT,
            tier TEXT,
            pca_x REAL,
            pca_y REAL
        );

        CREATE TABLE IF NOT EXISTS offers (
            id TEXT PRIMARY KEY,
            offer_type TEXT,
            reward INTEGER,
            difficulty INTEGER,
            duration INTEGER,
            channels TEXT
        );

        CREATE TABLE IF NOT EXISTS offer_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT,
            offer_id TEXT,
            received_time REAL,
            viewed_time REAL,
            completed_time REAL,
            was_viewed INTEGER,
            was_completed INTEGER,
            FOREIGN KEY (person) REFERENCES customers(id),
            FOREIGN KEY (offer_id) REFERENCES offers(id)
        );

        CREATE TABLE IF NOT EXISTS customer_pools (
            pool_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_name TEXT,
            criteria TEXT,
            member_count INTEGER,
            total_spend REAL,
            avg_income REAL,
            strategic_action TEXT
        );

        -- Performance Indexes
        CREATE INDEX IF NOT EXISTS idx_customers_cluster ON customers(cluster);
        CREATE INDEX IF NOT EXISTS idx_customers_spend ON customers(money_spent DESC);
        CREATE INDEX IF NOT EXISTS idx_offer_events_person ON offer_events(person);
        CREATE INDEX IF NOT EXISTS idx_offer_events_offer ON offer_events(offer_id);
    """)

    # 2. Seed Customers Table
    customer_df = ml_cache["customer_data_with_clusters"].copy()
    segment_profiles = ml_cache["segment_profiles"]

    customer_df["segment_name"] = customer_df["cluster"].map(lambda c: segment_profiles.get(c, {}).get("name", f"Cluster {c}"))
    customer_df["tier"] = customer_df["cluster"].map(lambda c: segment_profiles.get(c, {}).get("tier", "Core"))
    customer_df["became_member_on"] = customer_df["became_member_on"].astype(str)

    customer_records = []
    for _, r in customer_df.iterrows():
        customer_records.append((
            str(r["id"]),
            str(r["gender"]),
            int(r["age"]),
            float(r["income"]),
            str(r["became_member_on"])[:10],
            int(r["membership_days"]),
            int(r["num_received"]),
            int(r["num_viewed"]),
            int(r["num_completed"]),
            int(r["num_transactions"]),
            round(float(r["money_spent"]), 2),
            round(float(r["view_rate"]), 1),
            round(float(r["completion_rate"]), 1),
            round(float(r["avg_transaction_amount"]), 2),
            int(r["cluster"]),
            str(r["segment_name"]),
            str(r["tier"]),
            round(float(r.get("pca_x", 0.0)), 4),
            round(float(r.get("pca_y", 0.0)), 4)
        ))

    cursor.executemany("""
        INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, customer_records)

    # 3. Seed Offers Table
    portfolio_df = data_dict["portfolio"].copy()
    offer_records = []
    for _, r in portfolio_df.iterrows():
        channels_str = json.dumps(r["channels"] if isinstance(r["channels"], list) else eval(str(r["channels"])))
        offer_records.append((
            str(r["id"]),
            str(r["offer_type"]),
            int(r["reward"]),
            int(r["difficulty"]),
            int(r["duration"]),
            channels_str
        ))

    cursor.executemany("""
        INSERT OR REPLACE INTO offers VALUES (?,?,?,?,?,?)
    """, offer_records)

    # 4. Seed Offer Events Table
    offer_events_df = data_dict["offer_events"].copy()
    oe_records = []
    for _, r in offer_events_df.iterrows():
        oe_records.append((
            str(r["person"]),
            str(r["offer_id"]),
            float(r["received_time"]) if pd.notna(r["received_time"]) else None,
            float(r["viewed_time"]) if pd.notna(r["viewed_time"]) else None,
            float(r["completed_time"]) if pd.notna(r["completed_time"]) else None,
            int(r["was_viewed"]),
            int(r["was_completed"])
        ))

    cursor.executemany("""
        INSERT INTO offer_events (person, offer_id, received_time, viewed_time, completed_time, was_viewed, was_completed)
        VALUES (?,?,?,?,?,?,?)
    """, oe_records)

    # 5. Seed Customer Pools
    cdf = customer_df
    pool_records = [
        (
            "High-Value VIP Pool",
            "Total Spending >= $400 (Top 5% Revenue Spenders)",
            int((cdf["money_spent"] >= 400).sum()),
            float(round(cdf[cdf["money_spent"] >= 400]["money_spent"].sum(), 2)),
            float(round(cdf[cdf["money_spent"] >= 400]["income"].mean(), 0)),
            "Exclusive Reserve roasts, VIP tastings, high-difficulty high-reward promotions."
        ),
        (
            "Active Deal Seeker Pool",
            "Completion Rate >= 80% & Completed >= 3 offers",
            int(((cdf["completion_rate"] >= 80) & (cdf["num_completed"] >= 3)).sum()),
            float(round(cdf[(cdf["completion_rate"] >= 80) & (cdf["num_completed"] >= 3)]["money_spent"].sum(), 2)),
            float(round(cdf[(cdf["completion_rate"] >= 80) & (cdf["num_completed"] >= 3)]["income"].mean(), 0)),
            "Tiered Discount challenges, multi-day purchase challenges."
        ),
        (
            "Daily Habitual Regulars",
            "Store Transactions >= 12 visits",
            int((cdf["num_transactions"] >= 12).sum()),
            float(round(cdf[cdf["num_transactions"] >= 12]["money_spent"].sum(), 2)),
            float(round(cdf[cdf["num_transactions"] >= 12]["income"].mean(), 0)),
            "Morning beverage + food bundle cross-selling; weekly visit streak rewards."
        ),
        (
            "At-Risk / Dormant Pool",
            "Total Spending < $30 & Completed <= 1 offer",
            int(((cdf["money_spent"] < 30) & (cdf["num_completed"] <= 1)).sum()),
            float(round(cdf[(cdf["money_spent"] < 30) & (cdf["num_completed"] <= 1)]["money_spent"].sum(), 2)),
            float(round(cdf[(cdf["money_spent"] < 30) & (cdf["num_completed"] <= 1)]["income"].mean(), 0)),
            "Frictionless zero-cost informational messaging; halt expensive discount blasts."
        )
    ]

    cursor.execute("DELETE FROM customer_pools")
    cursor.executemany("""
        INSERT INTO customer_pools (pool_name, criteria, member_count, total_spend, avg_income, strategic_action)
        VALUES (?,?,?,?,?,?)
    """, pool_records)

    conn.commit()
    conn.close()
    logger.info("SQLite Database successfully initialized and seeded with all tables and indexes.")


def query_sample_customers_by_segment():
    """
    Returns a sample customer record for each segment to provide
    1-click instant pre-fill buttons for the user.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    samples = {}
    for cluster_id in range(5):
        cursor.execute("""
            SELECT * FROM customers
            WHERE cluster = ?
            ORDER BY money_spent DESC
            LIMIT 1 OFFSET 2
        """, (cluster_id,))
        row = cursor.fetchone()
        if row:
            samples[cluster_id] = dict(row)

    conn.close()
    return samples

