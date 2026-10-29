"""
data_processor.py — Data Loading & Processing Module
=====================================================
Loads, cleans, and processes the three Starbucks datasets.
Results are cached globally so data is not reloaded per request.
"""

import os
import ast
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(APP_DIR, "data")
PROFILE_FILE = os.path.join(BASE, "profile(1).csv")
PORTFOLIO_FILE = os.path.join(BASE, "portfolio(1).csv")
TRANSCRIPT_FILE = os.path.join(BASE, "transcript(1).csv")

# Global cache
_cached_data = None


def load_and_process_data(force_reload=False):
    """
    Load all 3 CSVs, clean them, build customer behavior table,
    merge with profile data. Caches result globally.

    Returns dict with keys:
        'profile', 'portfolio', 'transcript', 'customer_data', 'offer_events'
    """
    global _cached_data
    if _cached_data is not None and not force_reload:
        return _cached_data

    logger.info("Loading and processing data...")

    # --- Load raw data ---
    profile = pd.read_csv(PROFILE_FILE)
    portfolio = pd.read_csv(PORTFOLIO_FILE)
    transcript = pd.read_csv(TRANSCRIPT_FILE)

    # Drop unnecessary index columns
    for df in [profile, portfolio, transcript]:
        df.drop(columns=["Unnamed: 0"], errors="ignore", inplace=True)

    # --- Clean profile ---
    # age=118 is a sentinel for missing data in this dataset
    profile = profile[
        (profile["gender"].notna()) &
        (profile["income"].notna()) &
        (profile["age"] != 118)
    ].copy()
    profile.reset_index(drop=True, inplace=True)

    # Parse became_member_on to datetime and compute membership days
    profile["became_member_on"] = pd.to_datetime(
        profile["became_member_on"], format="%Y%m%d"
    )
    # Reference date: latest membership date in dataset
    ref_date = profile["became_member_on"].max()
    profile["membership_days"] = (ref_date - profile["became_member_on"]).dt.days

    # --- Parse transcript value column ---
    transcript = transcript.copy()
    transcript["value"] = transcript["value"].apply(ast.literal_eval)

    # Extract amount for transactions
    transcript["amount"] = transcript["value"].apply(
        lambda x: float(x.get("amount", 0) or 0)
    )

    # Extract offer_id from value dict
    transcript["offer_id"] = transcript["value"].apply(
        lambda x: x.get("offer id", x.get("offer_id", None))
    )

    # --- Build customer behavior ---
    valid_persons = set(profile["id"].values)
    transcript_valid = transcript[transcript["person"].isin(valid_persons)]

    received = (
        transcript_valid[transcript_valid["event"] == "offer received"]
        .groupby("person").size().rename("num_received")
    )
    viewed = (
        transcript_valid[transcript_valid["event"] == "offer viewed"]
        .groupby("person").size().rename("num_viewed")
    )
    completed = (
        transcript_valid[transcript_valid["event"] == "offer completed"]
        .groupby("person").size().rename("num_completed")
    )
    transactions = (
        transcript_valid[transcript_valid["event"] == "transaction"]
        .groupby("person").size().rename("num_transactions")
    )
    money_spent = (
        transcript_valid[transcript_valid["event"] == "transaction"]
        .groupby("person")["amount"].sum().rename("money_spent")
    )

    behavior = pd.concat(
        [received, viewed, completed, transactions, money_spent],
        axis=1
    ).fillna(0)

    # Derived behavior features
    behavior["view_rate"] = np.where(
        behavior["num_received"] > 0,
        behavior["num_viewed"] / behavior["num_received"] * 100,
        0
    )
    behavior["completion_rate"] = np.where(
        behavior["num_viewed"] > 0,
        behavior["num_completed"] / behavior["num_viewed"] * 100,
        0
    )
    behavior["avg_transaction_amount"] = np.where(
        behavior["num_transactions"] > 0,
        behavior["money_spent"] / behavior["num_transactions"],
        0
    )

    # --- Merge behavior with profile ---
    behavior.index.name = "id"
    behavior = behavior.reset_index()

    customer_data = profile.merge(behavior, left_on="id", right_on="id", how="left")
    # Fill NaN for customers with no transcript activity
    fill_cols = [
        "num_received", "num_viewed", "num_completed",
        "num_transactions", "money_spent", "view_rate",
        "completion_rate", "avg_transaction_amount"
    ]
    customer_data[fill_cols] = customer_data[fill_cols].fillna(0)

    # --- Build offer-level events ---
    offer_events = _build_offer_events(transcript_valid, valid_persons)

    # --- Clean portfolio channels ---
    portfolio["channels"] = portfolio["channels"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    _cached_data = {
        "profile": profile,
        "portfolio": portfolio,
        "transcript": transcript_valid,
        "customer_data": customer_data,
        "offer_events": offer_events,
    }

    logger.info(
        f"Data loaded: {len(customer_data)} customers, "
        f"{len(portfolio)} offers, {len(transcript_valid)} events"
    )
    return _cached_data


def _build_offer_events(transcript, valid_persons):
    """
    Build per-person, per-offer event tracking.
    For each person-offer pair, track whether the offer was received, viewed, completed,
    and the timestamps of each event.
    """
    offer_transcript = transcript[transcript["offer_id"].notna()].copy()

    # Group by person + offer_id + event
    events = offer_transcript.groupby(
        ["person", "offer_id", "event"]
    ).agg(
        count=("time", "size"),
        first_time=("time", "min"),
    ).reset_index()

    # Pivot to get columns for each event type
    received = events[events["event"] == "offer received"][
        ["person", "offer_id", "first_time"]
    ].rename(columns={"first_time": "received_time"})

    viewed = events[events["event"] == "offer viewed"][
        ["person", "offer_id", "first_time"]
    ].rename(columns={"first_time": "viewed_time"})

    completed = events[events["event"] == "offer completed"][
        ["person", "offer_id", "first_time"]
    ].rename(columns={"first_time": "completed_time"})

    # Merge into a single offer-events dataframe
    offer_events = received.merge(
        viewed, on=["person", "offer_id"], how="left"
    ).merge(
        completed, on=["person", "offer_id"], how="left"
    )

    offer_events["was_viewed"] = offer_events["viewed_time"].notna().astype(int)
    offer_events["was_completed"] = offer_events["completed_time"].notna().astype(int)

    return offer_events


def get_data():
    """Get the cached processed data, loading if necessary."""
    return load_and_process_data()


def get_customer_by_id(customer_id):
    """Look up a single customer by ID."""
    data = get_data()
    cdf = data["customer_data"]
    match = cdf[cdf["id"] == customer_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def get_customer_offers(customer_id):
    """Get all offer events for a specific customer."""
    data = get_data()
    oe = data["offer_events"]
    portfolio = data["portfolio"]

    customer_offers = oe[oe["person"] == customer_id].copy()
    if customer_offers.empty:
        return []

    # Merge with portfolio for offer details
    merged = customer_offers.merge(
        portfolio, left_on="offer_id", right_on="id", how="left",
        suffixes=("", "_offer")
    )

    results = []
    for _, row in merged.iterrows():
        results.append({
            "offer_id": row["offer_id"],
            "offer_type": row.get("offer_type", "unknown"),
            "reward": int(row.get("reward", 0)),
            "difficulty": int(row.get("difficulty", 0)),
            "duration": int(row.get("duration", 0)),
            "channels": row.get("channels", []),
            "received_time": float(row["received_time"]) if pd.notna(row["received_time"]) else None,
            "viewed_time": float(row["viewed_time"]) if pd.notna(row["viewed_time"]) else None,
            "completed_time": float(row["completed_time"]) if pd.notna(row["completed_time"]) else None,
            "was_viewed": bool(row["was_viewed"]),
            "was_completed": bool(row["was_completed"]),
        })

    return results


def get_customer_transactions(customer_id):
    """Get transaction history for a specific customer."""
    data = get_data()
    t = data["transcript"]
    txns = t[(t["person"] == customer_id) & (t["event"] == "transaction")]

    results = []
    for _, row in txns.iterrows():
        results.append({
            "time": int(row["time"]),
            "amount": round(float(row["amount"]), 2),
        })

    return sorted(results, key=lambda x: x["time"])


def search_customers(query, limit=20):
    """Search customers by ID prefix."""
    data = get_data()
    cdf = data["customer_data"]

    if not query:
        return []

    matches = cdf[cdf["id"].str.startswith(query, na=False)].head(limit)
    results = []
    for _, row in matches.iterrows():
        results.append({
            "id": row["id"],
            "gender": row["gender"],
            "age": int(row["age"]),
            "income": float(row["income"]),
        })
    return results

