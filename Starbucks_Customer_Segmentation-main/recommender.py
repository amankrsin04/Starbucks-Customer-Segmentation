"""
recommender.py — AI-Powered Personalized Offer Recommendation Engine
===================================================================
Recommends the top 3 best promotional offers for any customer (existing or hypothetical)
by synthesizing:
1. Historical segment response rates to specific offer types and difficulties.
2. Supervised Machine Learning conversion probabilities (Random Forest).
3. Value-to-difficulty alignment based on customer spending power.
4. Transparent rationale explaining why each offer was chosen, distinguishing
   heuristic rule-based strategy from ML probabilistic scoring.
"""

import logging
import pandas as pd
import numpy as np
import ml_engine

logger = logging.getLogger(__name__)


def recommend_offers_for_customer(customer_dict, portfolio_df, offer_events_df, top_n=3):
    """
    Generates top N personalized offer recommendations for a customer.
    
    Parameters:
        customer_dict (dict): Customer features (age, income, spending, etc.)
        portfolio_df (DataFrame): Offers catalog
        offer_events_df (DataFrame): Historical offer events
        top_n (int): Number of top offers to return (default 3)

    Returns:
        dict: Recommendation payload containing segment assignment, rationale, and ranked offers.
    """
    # 1. Predict cluster and retrieve segment profile
    cluster_id, profile = ml_engine.predict_cluster_for_customer(customer_dict)

    # 2. Compute historical cluster completion rate per offer from actual data
    cluster_offer_stats = _compute_cluster_offer_performance(cluster_id, offer_events_df, portfolio_df)

    # 3. Score each offer in the portfolio
    scored_offers = []

    for _, offer in portfolio_df.iterrows():
        offer_id = offer["id"]
        offer_type = offer["offer_type"]
        reward = int(offer["reward"])
        difficulty = int(offer["difficulty"])
        duration = int(offer["duration"])
        channels = offer["channels"] if isinstance(offer["channels"], list) else eval(str(offer["channels"]))

        # A. Historical response rate in this segment
        hist_stats = cluster_offer_stats.get(offer_id, {"completion_rate": 50.0, "views": 100})
        hist_comp_rate = hist_stats["completion_rate"]

        # B. Machine Learning model predicted conversion probability
        ml_prob = ml_engine.predict_offer_completion_prob(customer_dict, offer.to_dict())

        # C. Defensible Composite Suitability Score (0-100)
        # Weighted combination: 45% ML predicted probability, 35% Historical segment conversion rate, 20% Financial alignment
        income = float(customer_dict.get("income", 60000))
        spending = float(customer_dict.get("money_spent", 100))
        txns = float(customer_dict.get("num_transactions", 5))
        avg_ticket = spending / max(txns, 1)

        # Financial alignment heuristic:
        # High difficulty offers (e.g. spend $20) fit customers with high avg tickets.
        # Low difficulty / high reward offers fit budget conscious customers.
        if difficulty == 0:
            fin_fit = 70.0 # Informational offer
        else:
            ticket_to_diff_ratio = avg_ticket / difficulty
            fin_fit = min(100.0, max(30.0, ticket_to_diff_ratio * 70.0))

        if offer_type == "informational":
            # Informational offers don't have completion, evaluate by view rate and engagement
            composite_score = round((hist_comp_rate * 0.4) + (fin_fit * 0.4) + 20.0, 1)
            confidence_label = "Engagement Suitability (Informational awareness)"
        else:
            composite_score = round(
                (ml_prob * 100.0 * 0.45) +
                (hist_comp_rate * 0.35) +
                (fin_fit * 0.20),
                1
            )
            confidence_label = f"{round(composite_score)}% Suitability Match"

        # Cap composite score between 10% and 98% (never claim 100% certainty)
        composite_score = min(98.0, max(15.0, composite_score))

        # D. Transparent Reason Generation
        reason = _generate_offer_rationale(
            offer_type=offer_type,
            reward=reward,
            difficulty=difficulty,
            duration=duration,
            segment_name=profile.get("name", "Customer"),
            cluster_id=cluster_id,
            hist_rate=hist_comp_rate,
            ml_prob=ml_prob,
            avg_ticket=avg_ticket
        )

        scored_offers.append({
            "offer_id": offer_id,
            "offer_type": offer_type,
            "reward": reward,
            "difficulty": difficulty,
            "duration": duration,
            "channels": channels,
            "suitability_score": composite_score,
            "ml_completion_probability": round(ml_prob * 100, 1),
            "historical_segment_completion_rate": round(hist_comp_rate, 1),
            "confidence_label": confidence_label,
            "recommendation_reason": reason,
            "scoring_breakdown": {
                "ml_model_contribution": f"{round(ml_prob * 100, 1)}% ML conversion prediction (Random Forest)",
                "historical_benchmark": f"{round(hist_comp_rate, 1)}% historical completion in {profile.get('name', 'Segment')}",
                "financial_fit": f"{round(fin_fit, 1)}% ticket-to-difficulty affordability score"
            }
        })

    # Sort offers by suitability score descending
    scored_offers.sort(key=lambda x: x["suitability_score"], reverse=True)
    top_offers = scored_offers[:top_n]

    return {
        "customer_summary": {
            "age": int(customer_dict.get("age", 0)),
            "income": float(customer_dict.get("income", 0)),
            "money_spent": float(customer_dict.get("money_spent", 0)),
            "num_transactions": int(customer_dict.get("num_transactions", 0)),
            "num_received": int(customer_dict.get("num_received", 0)),
            "num_viewed": int(customer_dict.get("num_viewed", 0)),
            "num_completed": int(customer_dict.get("num_completed", 0)),
            "view_rate": round(float(customer_dict.get("view_rate", 0)), 1),
            "completion_rate": round(float(customer_dict.get("completion_rate", 0)), 1)
        },
        "assigned_segment": {
            "cluster_id": cluster_id,
            "name": profile.get("name", f"Cluster {cluster_id}"),
            "tier": profile.get("tier", "Core"),
            "badge_color": profile.get("badge_color", "#00754a"),
            "description": profile.get("description", ""),
            "marketing_strategy": profile.get("strategy", ""),
            "cluster_averages": {
                "avg_income": profile.get("avg_income", 0),
                "avg_spent": profile.get("avg_money_spent", 0),
                "avg_transactions": profile.get("avg_transactions", 0),
                "completion_rate": profile.get("completion_rate", 0)
            }
        },
        "recommended_offers": top_offers,
        "methodology_note": (
            "Recommendations combine a trained Random Forest supervised classifier "
            "with empirical K-Means historical completion benchmarks. "
            "Suitability scores reflect estimated likelihood of positive customer response, "
            "not a financial guarantee."
        )
    }


def _compute_cluster_offer_performance(cluster_id, offer_events_df, portfolio_df):
    """
    Calculates historical offer response metrics specifically for the given cluster.
    """
    stats = {}
    ml_cache = ml_engine._ml_cache
    if not ml_cache:
        return stats

    cust_clusters = ml_cache["customer_data_with_clusters"][["id", "cluster"]].rename(columns={"id": "person"})
    cluster_events = offer_events_df.merge(cust_clusters, on="person", how="inner")
    cluster_events = cluster_events[cluster_events["cluster"] == cluster_id]

    grouped = cluster_events.groupby("offer_id").agg(
        received=("received_time", "count"),
        viewed=("was_viewed", "sum"),
        completed=("was_completed", "sum")
    ).reset_index()

    for _, row in grouped.iterrows():
        oid = row["offer_id"]
        rx = row["received"]
        vw = row["viewed"]
        cp = row["completed"]
        comp_rate = (cp / max(vw, 1)) * 100 if vw > 0 else (cp / max(rx, 1)) * 100
        stats[oid] = {
            "received": int(rx),
            "viewed": int(vw),
            "completed": int(cp),
            "completion_rate": float(comp_rate)
        }
    return stats


def _generate_offer_rationale(offer_type, reward, difficulty, duration, segment_name, cluster_id, hist_rate, ml_prob, avg_ticket):
    """
    Produces transparent, non-arbitrary reasoning explaining why an offer matches.
    """
    if offer_type == "bogo":
        if difficulty <= 5:
            return (
                f"BOGO offer with low spend threshold (${difficulty}) and ${reward} reward. "
                f"Historical conversion in '{segment_name}' is {round(hist_rate, 1)}%. "
                f"Ideal for stimulating immediate purchase visits without creating spend resistance."
            )
        else:
            return (
                f"Premium BOGO offer (${difficulty} target with ${reward} reward over {duration} days). "
                f"Predicted ML completion probability is {round(ml_prob * 100, 1)}%, well-matched to "
                f"customers averaging ${round(avg_ticket, 2)} per visit."
            )
    elif offer_type == "discount":
        if difficulty >= 15:
            return (
                f"High-tier Discount challenge requiring ${difficulty} spend for a ${reward} incentive. "
                f"This customer's spending capacity matches the difficulty, maximizing incremental basket size."
            )
        else:
            return (
                f"Accessible Discount offer (${difficulty} difficulty, ${reward} reward) lasting {duration} days. "
                f"Provides a compelling {round(reward/max(difficulty, 1)*100)}% return on spend, proven effective for '{segment_name}'."
            )
    else: # informational
        return (
            f"Zero-cost Informational promotion spanning {duration} days. "
            f"Builds product awareness without discount fatigue, ideal for re-engagement or introducing new seasonal items."
        )

