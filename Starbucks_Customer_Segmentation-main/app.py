"""
app.py — Starbucks Customer Intelligence & Analytics Platform
=============================================================
Main Flask application entry point.
- Pre-warms datasets and machine learning models on initialization.
- Mounts RESTful API blueprint for dynamic SaaS analytics.
- Serves the Single-Page Application (SPA) dashboard.
- Maintains legacy POST form compatibility.
"""

import os
import logging
from flask import Flask, render_template, request, jsonify
from routes.api import api_bp
import data_processor
import ml_engine
import recommender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("StarbucksApp")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "starbucks_analytics_secret_key_2026")

# Register REST API blueprint
app.register_blueprint(api_bp)


# Pre-warm application state on startup
def init_app_state():
    try:
        logger.info("Pre-warming Starbucks analytics datasets and ML models...")
        data = data_processor.get_data()
        ml = ml_engine.train_or_load_models(data)
        import database
        database.init_and_seed_database(data, ml)
        logger.info(f"System ready: {len(data['customer_data'])} customers loaded, SQLite DB active, 5 clusters initialized.")
    except Exception as e:
        logger.error(f"Error initializing app state: {e}", exc_info=True)


with app.app_context():
    init_app_state()


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Primary interface route:
    - GET: Serves the modern, enterprise single-page analytics platform.
    - POST: Backwards-compatible handler for legacy form submissions.
    """
    if request.method == "GET":
        return render_template("index.html")

    # Legacy POST handler
    try:
        age = float(request.form.get("age", 35))
        income = float(request.form.get("income", 65000))
        received = float(request.form.get("received", 5))
        viewed = float(request.form.get("viewed", 4))
        completed = float(request.form.get("completed", 2))
        transactions = float(request.form.get("transactions", 8))
        money_spent = float(request.form.get("money_spent", 150))

        data = data_processor.get_data()
        cust_dict = {
            "age": age,
            "income": income,
            "gender": "F",
            "num_received": received,
            "num_viewed": viewed,
            "num_completed": completed,
            "num_transactions": transactions,
            "money_spent": money_spent
        }
        rec_res = recommender.recommend_offers_for_customer(
            cust_dict, data["portfolio"], data["offer_events"], top_n=1
        )

        top_offer = rec_res["recommended_offers"][0]
        assigned_seg = rec_res["assigned_segment"]

        view_rate = (viewed / received * 100) if received else 0
        completion_rate = (completed / viewed * 100) if viewed else 0

        return render_template(
            "result.html",
            age=int(age),
            income=f"{income:,.0f}",
            received=int(received),
            viewed=int(viewed),
            completed=int(completed),
            transactions=int(transactions),
            money_spent=f"{money_spent:,.2f}",
            view_rate=f"{view_rate:.1f}",
            completion_rate=f"{completion_rate:.1f}",
            cluster=assigned_seg["cluster_id"],
            segment=assigned_seg["name"],
            reason=top_offer["recommendation_reason"],
            offer=top_offer
        )
    except Exception as e:
        logger.error(f"Error in legacy post: {e}", exc_info=True)
        return render_template("index.html", error=f"Error: {e}")


@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "API endpoint not found"}), 404
    return render_template("index.html"), 404


@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    return render_template("index.html", error="Internal server error occurred"), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
