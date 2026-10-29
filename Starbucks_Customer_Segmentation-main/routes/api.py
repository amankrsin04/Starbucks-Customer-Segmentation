"""
routes/api.py — RESTful JSON API Endpoints
==========================================
Provides complete, robust API routes for:
- Dashboard KPIs
- Customer Segmentation & K-Means evaluation (Elbow, Silhouette, PCA)
- AI Offer Recommendations
- Promotional Campaign Performance & Funnel
- Customer 360° Profiles & Side-by-Side Comparator
- What-If Marketing Simulator
- Customer Pool Explorer & Correlation Matrix
- Automated Smart Marketing Insights
- CSV & Executive PDF Downloads
"""

import io
import logging
import pandas as pd
import numpy as np
from flask import Blueprint, jsonify, request, send_file, Response
import data_processor
import ml_engine
import recommender
import insights_engine
import report_generator

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _get_app_state():
    """Helper to ensure data and ML models are loaded."""
    data = data_processor.get_data()
    ml = ml_engine.train_or_load_models(data)
    return data, ml


# ==========================================
# 1. DASHBOARD OVERVIEW & KPIS
# ==========================================

@api_bp.route("/dashboard/summary", methods=["GET"])
def get_dashboard_summary():
    """Returns top-level KPIs and business metrics."""
    try:
        data, ml = _get_app_state()
        cdf = ml["customer_data_with_clusters"]
        transcript = data["transcript"]
        oe = data["offer_events"]
        portfolio = data["portfolio"]

        total_customers = int(len(cdf))
        total_txns = int(cdf["num_transactions"].sum())
        total_revenue = float(round(cdf["money_spent"].sum(), 2))
        avg_spend = float(round(cdf["money_spent"].mean(), 2))
        avg_income = float(round(cdf["income"].mean(), 0))
        avg_age = float(round(cdf["age"].mean(), 1))

        # Offers funnel
        total_received = int(len(oe))
        total_viewed = int(oe["was_viewed"].sum())
        total_completed = int(oe["was_completed"].sum())
        overall_view_rate = round((total_viewed / max(total_received, 1)) * 100, 1)
        overall_completion_rate = round((total_completed / max(total_viewed, 1)) * 100, 1)

        # Revenue by Segment
        seg_profiles = ml["segment_profiles"]
        segment_revenue = []
        for c_id, prof in seg_profiles.items():
            cluster_customers = cdf[cdf["cluster"] == c_id]
            c_rev = float(round(cluster_customers["money_spent"].sum(), 2))
            segment_revenue.append({
                "cluster_id": c_id,
                "name": prof["name"],
                "color": prof["badge_color"],
                "tier": prof["tier"],
                "members": prof["count"],
                "percentage": prof["percentage"],
                "revenue": c_rev,
                "revenue_share": round((c_rev / max(total_revenue, 1)) * 100, 1)
            })

        return jsonify({
            "status": "success",
            "kpis": {
                "total_customers": total_customers,
                "total_transactions": total_txns,
                "total_revenue": total_revenue,
                "avg_spend_per_customer": avg_spend,
                "avg_income": avg_income,
                "avg_age": avg_age,
                "total_offers_received": total_received,
                "total_offers_viewed": total_viewed,
                "total_offers_completed": total_completed,
                "overall_view_rate": overall_view_rate,
                "overall_completion_rate": overall_completion_rate,
                "active_campaigns": int(len(portfolio))
            },
            "segment_revenue_distribution": segment_revenue
        })
    except Exception as e:
        logger.error(f"Error in dashboard summary: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# 2. CUSTOMER SEGMENTATION & ML EVALUATION
# ==========================================

@api_bp.route("/segments", methods=["GET"])
def get_segments():
    """Returns all 5 customer segments with statistics and strategies."""
    try:
        _, ml = _get_app_state()
        profiles = list(ml["segment_profiles"].values())
        return jsonify({
            "status": "success",
            "count": len(profiles),
            "segments": profiles
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/segments/<int:segment_id>", methods=["GET"])
def get_segment_detail(segment_id):
    """Returns detailed statistics for a specific segment."""
    try:
        _, ml = _get_app_state()
        profiles = ml["segment_profiles"]
        if segment_id not in profiles:
            return jsonify({"status": "error", "message": "Segment not found"}), 404
        return jsonify({
            "status": "success",
            "segment": profiles[segment_id]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/segments/<int:segment_id>/customers", methods=["GET"])
def get_segment_customers(segment_id):
    """Paginated list of customers belonging to a cluster."""
    try:
        _, ml = _get_app_state()
        cdf = ml["customer_data_with_clusters"]

        cluster_df = cdf[cdf["cluster"] == segment_id]
        if cluster_df.empty and segment_id not in ml["segment_profiles"]:
            return jsonify({"status": "error", "message": "Invalid segment ID"}), 404

        # Search query
        search_q = request.args.get("search", "").strip().lower()
        if search_q:
            cluster_df = cluster_df[cluster_df["id"].str.lower().str.contains(search_q, na=False)]

        # Sorting
        sort_by = request.args.get("sort_by", "money_spent")
        order = request.args.get("order", "desc")
        ascending = (order.lower() == "asc")
        if sort_by in cluster_df.columns:
            cluster_df = cluster_df.sort_values(by=sort_by, ascending=ascending)

        # Pagination
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(5, int(request.args.get("per_page", 15))))
        total_records = len(cluster_df)
        total_pages = max(1, (total_records + per_page - 1) // per_page)

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_records = cluster_df.iloc[start_idx:end_idx]

        customers = []
        for _, row in page_records.iterrows():
            customers.append({
                "id": row["id"],
                "gender": row["gender"],
                "age": int(row["age"]),
                "income": float(row["income"]),
                "membership_days": int(row["membership_days"]),
                "money_spent": round(float(row["money_spent"]), 2),
                "num_transactions": int(row["num_transactions"]),
                "num_received": int(row["num_received"]),
                "num_viewed": int(row["num_viewed"]),
                "num_completed": int(row["num_completed"]),
                "view_rate": round(float(row["view_rate"]), 1),
                "completion_rate": round(float(row["completion_rate"]), 1)
            })

        return jsonify({
            "status": "success",
            "segment_id": segment_id,
            "segment_name": ml["segment_profiles"][segment_id]["name"],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages
            },
            "customers": customers
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/segments/comparison", methods=["GET"])
def get_segments_comparison():
    """Comparison matrix across segments for radar & bar charts."""
    try:
        _, ml = _get_app_state()
        profiles = ml["segment_profiles"]
        dimensions = ["avg_money_spent", "avg_transactions", "avg_income", "avg_completed", "completion_rate", "view_rate"]
        
        comparison = []
        for c_id, prof in profiles.items():
            comparison.append({
                "cluster_id": c_id,
                "name": prof["name"],
                "color": prof["badge_color"],
                "metrics": {dim: prof[dim] for dim in dimensions}
            })
        return jsonify({"status": "success", "comparison": comparison})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/ml/pca", methods=["GET"])
def get_pca_data():
    """PCA 2D projection scatter coordinates for cluster visualization."""
    try:
        points = ml_engine.get_pca_scatter_points(sample_size=1200)
        return jsonify({"status": "success", "sample_count": len(points), "points": points})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/ml/elbow", methods=["GET"])
def get_elbow_data():
    """Returns K-Means Elbow inertias and Silhouette scores."""
    try:
        _, ml = _get_app_state()
        m = ml["metrics"]
        return jsonify({
            "status": "success",
            "k_values": m["elbow_k"],
            "inertias": m["elbow_inertias"],
            "silhouette_scores": m["silhouette_scores"],
            "selected_k": m["selected_k"]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/ml/metrics", methods=["GET"])
def get_ml_metrics():
    """Supervised model evaluation metrics (Random Forest)."""
    try:
        _, ml = _get_app_state()
        return jsonify({
            "status": "success",
            "supervised_metrics": ml["metrics"]["supervised_model"],
            "pca_variance": ml["metrics"]["pca_variance_explained"]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# 3. OFFER RECOMMENDATION SYSTEM
# ==========================================

@api_bp.route("/recommend", methods=["POST"])
def get_recommendation():
    """
    Accepts customer profile parameters and returns top 3 recommended offers
    with full transparent justification.
    """
    try:
        data, _ = _get_app_state()
        portfolio = data["portfolio"]
        oe = data["offer_events"]

        payload = request.get_json() or {}
        # Clean inputs
        customer_dict = {
            "age": float(payload.get("age", 40)),
            "income": float(payload.get("income", 60000)),
            "gender": str(payload.get("gender", "M")).upper(),
            "num_received": float(payload.get("received", payload.get("num_received", 4))),
            "num_viewed": float(payload.get("viewed", payload.get("num_viewed", 3))),
            "num_completed": float(payload.get("completed", payload.get("num_completed", 2))),
            "num_transactions": float(payload.get("transactions", payload.get("num_transactions", 8))),
            "money_spent": float(payload.get("money_spent", 120.0)),
        }
        customer_dict["view_rate"] = (
            (customer_dict["num_viewed"] / customer_dict["num_received"] * 100)
            if customer_dict["num_received"] > 0 else 0
        )
        customer_dict["completion_rate"] = (
            (customer_dict["num_completed"] / customer_dict["num_viewed"] * 100)
            if customer_dict["num_viewed"] > 0 else 0
        )

        result = recommender.recommend_offers_for_customer(
            customer_dict, portfolio, oe, top_n=3
        )
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        logger.error(f"Error in recommendation: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/recommend/customer/<customer_id>", methods=["GET"])
def recommend_for_existing_customer(customer_id):
    """Generates recommendations for an actual dataset customer by ID."""
    try:
        data, _ = _get_app_state()
        cust = data_processor.get_customer_by_id(customer_id)
        if not cust:
            return jsonify({"status": "error", "message": f"Customer ID '{customer_id}' not found"}), 404

        portfolio = data["portfolio"]
        oe = data["offer_events"]

        result = recommender.recommend_offers_for_customer(cust, portfolio, oe, top_n=3)
        return jsonify({"status": "success", "customer_id": customer_id, "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/customers/search", methods=["GET"])
def search_customers_route():
    """Autocomplete search for customers by ID prefix."""
    try:
        q = request.args.get("q", "").strip()
        results = data_processor.search_customers(q, limit=15)
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/samples", methods=["GET"])
def get_sample_customers():
    """Returns representative real customers across all 5 clusters for instant UI loading."""
    try:
        import database
        samples = database.query_sample_customers_by_segment()
        return jsonify({"status": "success", "samples": samples})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# 4. CAMPAIGN PERFORMANCE ANALYTICS
# ==========================================

@api_bp.route("/campaigns/overview", methods=["GET"])
def get_campaigns_overview():
    """Overall promotional funnel and performance aggregations."""
    try:
        data, _ = _get_app_state()
        oe = data["offer_events"]
        port = data["portfolio"]

        total_rx = len(oe)
        total_vw = int(oe["was_viewed"].sum())
        total_cp = int(oe["was_completed"].sum())

        return jsonify({
            "status": "success",
            "funnel": {
                "received": total_rx,
                "viewed": total_vw,
                "completed": total_cp,
                "drop_after_received": total_rx - total_vw,
                "drop_after_viewed": total_vw - total_cp,
                "view_rate": round((total_vw / max(total_rx, 1)) * 100, 1),
                "completion_rate": round((total_cp / max(total_vw, 1)) * 100, 1),
                "overall_conversion_rate": round((total_cp / max(total_rx, 1)) * 100, 1)
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/campaigns/offers", methods=["GET"])
def get_all_campaign_offers():
    """Detailed performance metrics for each of the 10 portfolio offers."""
    try:
        data, _ = _get_app_state()
        oe = data["offer_events"]
        port = data["portfolio"]

        valid_events = oe.merge(port, left_on="offer_id", right_on="id", how="inner")
        grouped = valid_events.groupby(["offer_id", "offer_type", "difficulty", "reward", "duration"]).agg(
            received=("received_time", "count"),
            viewed=("was_viewed", "sum"),
            completed=("was_completed", "sum")
        ).reset_index()

        grouped["view_rate"] = (grouped["viewed"] / grouped["received"] * 100).round(1)
        grouped["completion_rate"] = np.where(
            grouped["offer_type"] == "informational",
            0.0,
            (grouped["completed"] / grouped["viewed"] * 100).round(1)
        )

        offers_list = []
        for _, row in grouped.iterrows():
            oid = row["offer_id"]
            # lookup channels
            match = port[port["id"] == oid]
            channels = match.iloc[0]["channels"] if not match.empty else []

            offers_list.append({
                "offer_id": oid,
                "offer_type": row["offer_type"],
                "difficulty": int(row["difficulty"]),
                "reward": int(row["reward"]),
                "duration": int(row["duration"]),
                "channels": channels,
                "received": int(row["received"]),
                "viewed": int(row["viewed"]),
                "completed": int(row["completed"]),
                "view_rate": float(row["view_rate"]),
                "completion_rate": float(row["completion_rate"])
            })

        # Sort by completion rate descending
        offers_list.sort(key=lambda x: x["completion_rate"], reverse=True)
        return jsonify({"status": "success", "count": len(offers_list), "offers": offers_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/campaigns/by-type", methods=["GET"])
def get_campaigns_by_type():
    """Performance breakdown by offer type (BOGO vs Discount vs Informational)."""
    try:
        data, _ = _get_app_state()
        oe = data["offer_events"]
        port = data["portfolio"]

        merged = oe.merge(port[["id", "offer_type"]], left_on="offer_id", right_on="id")
        grouped = merged.groupby("offer_type").agg(
            received=("received_time", "count"),
            viewed=("was_viewed", "sum"),
            completed=("was_completed", "sum")
        ).reset_index()

        results = []
        for _, row in grouped.iterrows():
            rx = int(row["received"])
            vw = int(row["viewed"])
            cp = int(row["completed"])
            vr = round((vw / max(rx, 1)) * 100, 1)
            cr = round((cp / max(vw, 1)) * 100, 1) if row["offer_type"] != "informational" else 0.0

            results.append({
                "offer_type": row["offer_type"].upper(),
                "received": rx,
                "viewed": vw,
                "completed": cp,
                "view_rate": vr,
                "completion_rate": cr
            })
        return jsonify({"status": "success", "by_type": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/campaigns/by-segment", methods=["GET"])
def get_campaigns_by_segment():
    """Cross-tabulation of completion rates: Segment vs Offer Type."""
    try:
        data, ml = _get_app_state()
        oe = data["offer_events"]
        port = data["portfolio"]
        cust_clusters = ml["customer_data_with_clusters"][["id", "cluster"]].rename(columns={"id": "person"})

        merged = oe.merge(cust_clusters, on="person", how="inner").merge(port[["id", "offer_type"]], left_on="offer_id", right_on="id")
        non_info = merged[merged["offer_type"] != "informational"]

        matrix = []
        seg_profiles = ml["segment_profiles"]

        for c_id, prof in seg_profiles.items():
            c_events = non_info[non_info["cluster"] == c_id]
            bogo_sub = c_events[c_events["offer_type"] == "bogo"]
            disc_sub = c_events[c_events["offer_type"] == "discount"]

            bogo_cr = round((bogo_sub["was_completed"].sum() / max(bogo_sub["was_viewed"].sum(), 1)) * 100, 1)
            disc_cr = round((disc_sub["was_completed"].sum() / max(disc_sub["was_viewed"].sum(), 1)) * 100, 1)

            matrix.append({
                "cluster_id": c_id,
                "segment_name": prof["name"],
                "badge_color": prof["badge_color"],
                "bogo_completion_rate": bogo_cr,
                "discount_completion_rate": disc_cr
            })
        return jsonify({"status": "success", "matrix": matrix})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# 5. INDIVIDUAL CUSTOMER 360° PROFILE
# ==========================================

@api_bp.route("/customer/<customer_id>", methods=["GET"])
def get_customer_profile(customer_id):
    """Full 360-degree customer intelligence profile."""
    try:
        data, ml = _get_app_state()
        cust = data_processor.get_customer_by_id(customer_id)
        if not cust:
            return jsonify({"status": "error", "message": f"Customer ID '{customer_id}' not found"}), 404

        cluster_id, profile = ml_engine.predict_cluster_for_customer(cust)
        offers = data_processor.get_customer_offers(customer_id)
        txns = data_processor.get_customer_transactions(customer_id)

        # Spending timeline aggregation (group by 50-hour intervals)
        time_buckets = {}
        for t in txns:
            b = (t["time"] // 50) * 50
            time_buckets[b] = round(time_buckets.get(b, 0.0) + t["amount"], 2)

        spending_timeline = [
            {"hour": k, "amount": v} for k, v in sorted(time_buckets.items())
        ]

        return jsonify({
            "status": "success",
            "customer": {
                "id": cust["id"],
                "gender": cust["gender"],
                "age": int(cust["age"]),
                "income": float(cust["income"]),
                "became_member_on": str(cust["became_member_on"])[:10],
                "membership_days": int(cust["membership_days"]),
                "num_transactions": int(cust["num_transactions"]),
                "money_spent": round(float(cust["money_spent"]), 2),
                "avg_transaction_amount": round(float(cust["avg_transaction_amount"]), 2),
                "num_received": int(cust["num_received"]),
                "num_viewed": int(cust["num_viewed"]),
                "num_completed": int(cust["num_completed"]),
                "view_rate": round(float(cust["view_rate"]), 1),
                "completion_rate": round(float(cust["completion_rate"]), 1),
                "cluster_id": cluster_id,
                "segment_name": profile.get("name", "Cluster"),
                "tier": profile.get("tier", "Core"),
                "badge_color": profile.get("badge_color", "#00754a"),
                "marketing_strategy": profile.get("strategy", "")
            },
            "offer_history": offers,
            "transaction_count": len(txns),
            "spending_timeline": spending_timeline
        })
    except Exception as e:
        logger.error(f"Error in customer 360: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/customer/compare", methods=["GET"])
def compare_customers():
    """Side-by-side comparison of two customers."""
    try:
        id1 = request.args.get("id1", "").strip()
        id2 = request.args.get("id2", "").strip()

        if not id1 or not id2:
            return jsonify({"status": "error", "message": "Both id1 and id2 parameters required"}), 400

        c1 = data_processor.get_customer_by_id(id1)
        c2 = data_processor.get_customer_by_id(id2)

        if not c1 or not c2:
            return jsonify({"status": "error", "message": "One or both customer IDs were not found"}), 404

        _, ml = _get_app_state()
        c1_cluster, c1_prof = ml_engine.predict_cluster_for_customer(c1)
        c2_cluster, c2_prof = ml_engine.predict_cluster_for_customer(c2)

        return jsonify({
            "status": "success",
            "customer_1": {
                "id": c1["id"],
                "age": int(c1["age"]),
                "income": float(c1["income"]),
                "gender": c1["gender"],
                "money_spent": round(float(c1["money_spent"]), 2),
                "num_transactions": int(c1["num_transactions"]),
                "num_completed": int(c1["num_completed"]),
                "view_rate": round(float(c1["view_rate"]), 1),
                "completion_rate": round(float(c1["completion_rate"]), 1),
                "segment_name": c1_prof.get("name", "Cluster 1"),
                "badge_color": c1_prof.get("badge_color", "#00754a")
            },
            "customer_2": {
                "id": c2["id"],
                "age": int(c2["age"]),
                "income": float(c2["income"]),
                "gender": c2["gender"],
                "money_spent": round(float(c2["money_spent"]), 2),
                "num_transactions": int(c2["num_transactions"]),
                "num_completed": int(c2["num_completed"]),
                "view_rate": round(float(c2["view_rate"]), 1),
                "completion_rate": round(float(c2["completion_rate"]), 1),
                "segment_name": c2_prof.get("name", "Cluster 2"),
                "badge_color": c2_prof.get("badge_color", "#00754a")
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# 6. WHAT-IF MARKETING SIMULATOR
# ==========================================

@api_bp.route("/simulator/run", methods=["POST"])
def run_what_if_simulation():
    """
    Simulates campaign outcome based on selected customer segment pool,
    offer economics, and marketing budget.
    """
    try:
        data, ml = _get_app_state()
        payload = request.get_json() or {}

        segment_id = int(payload.get("segment_id", 0))
        offer_type = str(payload.get("offer_type", "discount")).lower()
        reward = float(payload.get("reward", 3))
        difficulty = float(payload.get("difficulty", 7))
        duration = float(payload.get("duration", 7))
        target_audience_size = int(payload.get("audience_size", 2000))
        budget = float(payload.get("budget", 5000))

        profiles = ml["segment_profiles"]
        if segment_id not in profiles:
            target_profile = profiles[0]
            segment_id = 0
        else:
            target_profile = profiles[segment_id]

        pool_total_members = target_profile["count"]
        # Audience cannot exceed segment size
        actual_audience = min(target_audience_size, pool_total_members)

        # Baseline view rate for this segment
        base_view_rate = target_profile["view_rate"] / 100.0
        # Simulated views
        est_views = int(round(actual_audience * base_view_rate))

        # Model predicted completion probability using representative customer from segment
        mock_customer = {
            "age": target_profile["avg_age"],
            "income": target_profile["avg_income"],
            "membership_days": 650,
            "num_transactions": target_profile["avg_transactions"],
            "money_spent": target_profile["avg_money_spent"],
            "avg_transaction_amount": target_profile["avg_money_spent"] / max(target_profile["avg_transactions"], 1),
            "gender": "F"
        }
        mock_offer = {
            "offer_type": offer_type,
            "reward": reward,
            "difficulty": difficulty,
            "duration": duration
        }

        prob_completion = ml_engine.predict_offer_completion_prob(mock_customer, mock_offer)
        est_completions = int(round(est_views * prob_completion))

        # Financial estimations (Transparent Assumptions)
        # Cost: Reward payout + communication dispatch cost ($0.05 per recipient)
        comm_cost = actual_audience * 0.05
        reward_cost = est_completions * reward
        est_total_cost = round(comm_cost + reward_cost, 2)

        # Gross Revenue: Completions require at least spending equal to difficulty threshold
        est_gross_revenue = round(est_completions * max(difficulty, target_profile["avg_money_spent"] / max(target_profile["avg_transactions"], 1)), 2)
        net_profit = round(est_gross_revenue - est_total_cost, 2)
        roi_pct = round((net_profit / max(est_total_cost, 1.0)) * 100, 1)

        # Budget sufficiency check
        budget_status = "Adequate" if budget >= est_total_cost else f"Exceeded by ${round(est_total_cost - budget, 2)}"

        return jsonify({
            "status": "success",
            "simulation": {
                "segment_name": target_profile["name"],
                "target_audience_size": actual_audience,
                "segment_coverage_pct": round((actual_audience / max(pool_total_members, 1)) * 100, 1),
                "estimated_views": est_views,
                "estimated_view_rate": round(base_view_rate * 100, 1),
                "estimated_completions": est_completions,
                "estimated_completion_rate": round(prob_completion * 100, 1),
                "estimated_campaign_cost": est_total_cost,
                "estimated_gross_revenue": est_gross_revenue,
                "estimated_net_profit": net_profit,
                "estimated_roi_percentage": roi_pct,
                "budget_check": {
                    "allocated_budget": budget,
                    "estimated_cost": est_total_cost,
                    "status": budget_status
                },
                "assumptions": [
                    "Estimated views derived from historical view rates of the target segment.",
                    "Offer completion probability forecasted via Random Forest classifier trained on 55,000+ offer events.",
                    "Estimated revenue assumes customer spends at least the challenge difficulty threshold or their average ticket.",
                    "Communication dispatch assumed at $0.05 per member reached.",
                    "Figures are statistical estimates for strategic scenario modeling and do not constitute guaranteed revenue."
                ]
            }
        })
    except Exception as e:
        logger.error(f"Error in simulation: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# 7. CUSTOMER DATA EXPLORER & POOLS
# ==========================================

@api_bp.route("/explorer/demographics", methods=["GET"])
def get_demographics_distribution():
    """Customer demographic distributions: age brackets, income tiers, gender."""
    try:
        _, ml = _get_app_state()
        cdf = ml["customer_data_with_clusters"]

        # Age brackets
        age_bins = [18, 30, 45, 60, 75, 105]
        age_labels = ["18-29", "30-44", "45-59", "60-74", "75+"]
        age_counts = pd.cut(cdf["age"], bins=age_bins, labels=age_labels, right=False).value_counts().to_dict()

        # Income brackets
        inc_bins = [30000, 50000, 70000, 90000, 125000]
        inc_labels = ["$30k-$49k", "$50k-$69k", "$70k-$89k", "$90k+"]
        inc_counts = pd.cut(cdf["income"], bins=inc_bins, labels=inc_labels, right=False).value_counts().to_dict()

        # Gender
        gender_counts = cdf["gender"].value_counts().to_dict()

        return jsonify({
            "status": "success",
            "age_distribution": [{"bracket": k, "count": int(v)} for k, v in age_counts.items()],
            "income_distribution": [{"bracket": k, "count": int(v)} for k, v in inc_counts.items()],
            "gender_distribution": [{"gender": k, "count": int(v)} for k, v in gender_counts.items()]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/explorer/correlations", methods=["GET"])
def get_correlations():
    """Pearson correlation matrix across continuous metrics."""
    try:
        _, ml = _get_app_state()
        cdf = ml["customer_data_with_clusters"]
        cols = ["money_spent", "num_transactions", "income", "age", "num_completed", "view_rate", "completion_rate"]
        corr = cdf[cols].corr().round(3).to_dict()

        matrix = []
        for c1 in cols:
            row = {"feature": c1}
            for c2 in cols:
                row[c2] = corr[c1][c2]
            matrix.append(row)

        return jsonify({"status": "success", "features": cols, "correlation_matrix": matrix})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/pools", methods=["GET"])
@api_bp.route("/explorer/pools", methods=["GET"])
def get_customer_pools():
    """
    Cohort and behavioral pool analysis requested by user.
    Groups members into actionable pools (VIP, Deal Seekers, Frequency Regulars, At-Risk).
    """
    try:
        _, ml = _get_app_state()
        cdf = ml["customer_data_with_clusters"]

        pools = [
            {
                "pool_name": "High-Value VIP Pool",
                "criteria": "Total Spending > $400 or Top 5% Spenders",
                "count": int((cdf["money_spent"] >= 400).sum()),
                "total_spend": float(round(cdf[cdf["money_spent"] >= 400]["money_spent"].sum(), 2)),
                "avg_income": float(round(cdf[cdf["money_spent"] >= 400]["income"].mean(), 0)),
                "action": "Enroll in Premium Reserve tastings & concierge rewards."
            },
            {
                "pool_name": "Active Deal Seeker Pool",
                "criteria": "Offer Completion Rate >= 80% & Completed >= 3 offers",
                "count": int(((cdf["completion_rate"] >= 80) & (cdf["num_completed"] >= 3)).sum()),
                "total_spend": float(round(cdf[(cdf["completion_rate"] >= 80) & (cdf["num_completed"] >= 3)]["money_spent"].sum(), 2)),
                "avg_income": float(round(cdf[(cdf["completion_rate"] >= 80) & (cdf["num_completed"] >= 3)]["income"].mean(), 0)),
                "action": "Target with multi-day challenge discount passes."
            },
            {
                "pool_name": "Daily Habitual Regulars",
                "criteria": "Transactions >= 12 visits during campaign window",
                "count": int((cdf["num_transactions"] >= 12).sum()),
                "total_spend": float(round(cdf[cdf["num_transactions"] >= 12]["money_spent"].sum(), 2)),
                "avg_income": float(round(cdf[cdf["num_transactions"] >= 12]["income"].mean(), 0)),
                "action": "Breakfast food bundle pairing and morning visit streaks."
            },
            {
                "pool_name": "At-Risk / Dormant Pool",
                "criteria": "Total Spend < $30 & Completed <= 1 offer",
                "count": int(((cdf["money_spent"] < 30) & (cdf["num_completed"] <= 1)).sum()),
                "total_spend": float(round(cdf[(cdf["money_spent"] < 30) & (cdf["num_completed"] <= 1)]["money_spent"].sum(), 2)),
                "avg_income": float(round(cdf[(cdf["money_spent"] < 30) & (cdf["num_completed"] <= 1)]["income"].mean(), 0)),
                "action": "Zero-cost awareness messaging; halt high-cost promotional blasts."
            }
        ]
        return jsonify({"status": "success", "pools": pools})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# 8. SMART ACTIONABLE INSIGHTS
# ==========================================

@api_bp.route("/insights", methods=["GET"])
def get_insights():
    """Returns automated data-driven insights."""
    try:
        data, ml = _get_app_state()
        category = request.args.get("category", None)
        insights = insights_engine.generate_marketing_insights(data, ml)

        if category:
            insights = [i for i in insights if i["category"] == category]

        return jsonify({"status": "success", "count": len(insights), "insights": insights})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# 9. EXPORTS & DOWNLOADABLE REPORTS
# ==========================================

@api_bp.route("/export/customers/csv", methods=["GET"])
def export_customers_csv():
    """Generates dynamic CSV file of customers with optional segment filter."""
    try:
        _, ml = _get_app_state()
        cdf = ml["customer_data_with_clusters"].copy()

        seg = request.args.get("segment", None)
        if seg is not None and seg != "":
            seg_id = int(seg)
            cdf = cdf[cdf["cluster"] == seg_id]

        # Map cluster names
        profiles = ml["segment_profiles"]
        cdf["segment_name"] = cdf["cluster"].map(lambda x: profiles.get(x, {}).get("name", f"Cluster {x}"))

        output_cols = [
            "id", "gender", "age", "income", "membership_days",
            "cluster", "segment_name", "money_spent", "num_transactions",
            "num_received", "num_viewed", "num_completed",
            "view_rate", "completion_rate"
        ]
        export_df = cdf[output_cols]

        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        filename = f"starbucks_customers_segment_{seg if seg else 'all'}.csv"
        return Response(
            csv_buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error in CSV export: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/export/report/pdf", methods=["GET"])
def export_pdf_report():
    """Generates and streams executive PDF report."""
    try:
        data, ml = _get_app_state()
        seg_param = request.args.get("segment", None)
        segment_filter = int(seg_param) if (seg_param is not None and seg_param != "") else None

        pdf_bytes = report_generator.generate_executive_pdf_report(data, ml, segment_filter=segment_filter)
        filename = f"Starbucks_Analytics_Executive_Report_{'Segment_' + str(segment_filter) if segment_filter is not None else 'All'}.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error in PDF generation: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

