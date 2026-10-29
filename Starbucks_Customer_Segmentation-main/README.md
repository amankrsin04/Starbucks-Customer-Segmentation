# ☕ Starbucks Promotional Campaign Analytics & Customer Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green.svg)](https://palletsprojects.com/p/flask/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.8.0-orange.svg)](https://scikit-learn.org/)
[![Pandas](https://img.shields.io/badge/Pandas-3.0.2-darkblue.svg)](https://pandas.pydata.org/)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4.1-coral.svg)](https://www.chartjs.org/)

An enterprise-grade, AI-powered Business Intelligence (BI) and Customer Analytics Platform built on Starbucks Rewards transaction and promotional campaign event data. 

The application combines **Unsupervised K-Means Clustering** with **Supervised Random Forest Conversion Forecasting**, interactive multi-dimensional visualizations, a **What-If Campaign Scenario Simulator**, and dynamic **Automated PDF Executive Reporting**.

---

## 🚀 Key Features

### 1. Advanced Customer Segmentation Dashboard
* **Standardized Clustering:** Multi-feature K-Means clustering ($k=5$) with `StandardScaler` scaling on income, age, transaction frequency, total spending, and promotional response metrics.
* **Empirical Validation:** Dual statistical justification via **Elbow Method (Inertia)** and **Silhouette Scores** across $k=2$ to $k=8$.
* **Data-Driven Segment Naming:** Non-arbitrary segment titles and behavioral profiles derived from actual cluster centroids:
  * 🟢 **High-Value VIP Spenders:** Highest spending power ($785+ avg), near-perfect completion (97.3%).
  * 🔵 **Frequent Everyday Loyalists:** Habitual daily visitors (15+ visits/month), 86.5% completion rate.
  * 🌿 **Affluent Offer Enthusiasts:** Upper-bracket income ($84k+ avg), highly responsive to promotions.
  * 🟡 **Selective Occasionals:** Moderate spending ($80 avg), selective discount seekers.
  * 🔴 **Low-Engagement / At-Risk Pool:** Low activity ($28 avg spend, 21.9% completion), churn hazard.
* **PCA 2D Cluster Projection:** Interactive scatter plot with hover inspectability mapping customer records across two principal components.
* **Segment Inspector & Member Table:** Search, sort, and paginate through customer records per cluster, with one-click CSV export.

### 2. AI-Powered Personalized Offer Recommendation
* **Dual Input Modes:** Input custom hypothetical customer parameters or look up actual customers by dataset ID with autocomplete.
* **Two-Tier Recommendation Engine:**
  1. *K-Means Classification:* Predicts assigned segment and retrieves historical cohort response benchmarks.
  2. *Supervised Machine Learning:* Employs a trained **Random Forest Classifier** (`ROC-AUC: 0.9027`, `Accuracy: 83.68%`) to forecast conversion probability for each offer in the portfolio without data leakage.
  3. *Financial Fit Affordability:* Matches customer average ticket size to offer difficulty threshold.
* **Top 3 Ranked Offers:** Displays suitability match scores, confidence metrics, and transparent, natural language explanations distinguishing heuristic segment strategy from probabilistic ML predictions.

### 3. Promotional Campaign Performance Analytics
* **Full Campaign Funnel:** Audited tracking of **Offer Received $\rightarrow$ Offer Viewed $\rightarrow$ Offer Completed**.
* **10-Offer Catalog Matrix:** Real-time breakdown of view rates and completion rates for every official Starbucks offer.
* **Elasticity & Channel Breakdown:** Comparative evaluation across offer types (**BOGO** vs **Discount** vs **Informational**) and channel distribution (4-channel vs 2-channel reach).

### 4. Individual Customer 360° Profile & Comparator
* **Customer Journey Timeline:** Visual log of every offer event with timestamps (`T+0h`, `T+168h`), view status, and completion state.
* **Spending Trend:** Hourly spending distribution line chart across the 714-hour monitoring window.
* **Side-by-Side Comparator:** Compare two actual customer profiles simultaneously across spending, visits, and campaign responsiveness.

### 5. Interactive What-If Marketing Simulator
* **Scenario Planning:** Select target customer pool, offer format, reward ($), difficulty ($), duration (days), audience size, and campaign budget.
* **Real-Time Outcome Projections:** Forecasts estimated views, completions, total campaign costs, gross revenue, net profit, and ROI %.
* **Budget Sufficiency Meter:** Automatically validates whether allocated budget covers communication dispatch and reward liability.
* **Transparent Assumptions:** Discloses all econometric formulas and data boundaries.

### 6. Customer Pools & Cohort Explorer
* **Actionable Cohort Pools:**
  * *High-Value VIP Pool:* Spenders with $\$400+$ lifetime spend.
  * *Active Deal Seeker Pool:* Members with $\ge 80\%$ completion rate on $\ge 3$ offers.
  * *Daily Habitual Regulars:* Customers with $\ge 12$ monthly visits.
  * *At-Risk / Dormant Pool:* Spend $<\$30$ and completed $\le 1$ offer.
* **Demographic Pyramids:** Age bracket distribution and income tier histograms.
* **Pearson Correlation Matrix:** Color-coded correlation heatmap across continuous features.

### 7. Downloadable Reports & Data Export
* **Executive PDF Report:** Dynamically generated using `fpdf2` featuring Starbucks branding, platform KPIs, cluster summaries, campaign tables, strategic findings, and ML audit metrics.
* **Custom Segment CSV Export:** Download filtered customer records for CRM or marketing automation ingest.

### 8. Smart Marketing Insights Engine
* Automatically synthesizes data into categorized insight cards (**Revenue Disparity**, **Discount vs BOGO ROI**, **Dormant Pool Waste**, **Omnichannel Lift**, **Affluent Pricing Tolerance**).

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend & REST API** | Python 3.11+, Flask 3.1.3, Blueprints, Gunicorn |
| **Data Processing** | Pandas 3.0.2, NumPy 2.4.6, AST |
| **Machine Learning** | Scikit-Learn 1.8.0 (`KMeans`, `StandardScaler`, `PCA`, `RandomForestClassifier`), Joblib |
| **PDF Reporting** | fpdf2 2.8.9 |
| **Frontend UI/UX** | Modern Semantic HTML5, CSS3 Custom Properties, Responsive Flexbox/Grid |
| **Data Visualization** | Chart.js 4.4.1 (Doughnut, Bar, Scatter PCA, Radar, Line) |

---

## 📂 Project Architecture

```text
Starbucks_Customer_Segmentation-main/
│
├── app.py                      # Flask application entry point & route initialization
├── data_processor.py           # Data loading, cleaning, behavior aggregation, caching
├── ml_engine.py                # Scaling, K-Means, PCA, Random Forest model, metrics
├── recommender.py              # Multi-factor personalized offer recommendation engine
├── insights_engine.py          # Deterministic, data-driven marketing insights generator
├── report_generator.py         # Dynamic executive PDF generator (fpdf2)
├── requirements.txt            # Python dependencies
│
├── data/
│   ├── portfolio(1).csv        # 10 Starbucks promotional offers metadata
│   ├── profile(1).csv          # 17,000 customer demographic profiles
│   └── transcript(1).csv       # 306,534 transactional and offer event logs
│
├── models/                     # Persisted trained ML artifacts (Joblib)
│   ├── kmeans_cluster_model.joblib
│   ├── kmeans_scaler.joblib
│   ├── pca_transformer.joblib
│   ├── offer_conversion_rf.joblib
│   ├── rf_preprocessor.joblib
│   └── ml_evaluation_metrics.joblib
│
├── routes/
│   └── api.py                  # RESTful JSON API endpoints (/api/*)
│
├── static/
│   ├── style.css               # Starbucks enterprise design system & dark mode
│   └── js/
│       └── app.js              # Client controller, chart rendering, AJAX calls
│
└── templates/
    ├── index.html              # Main Single-Page Application (SPA) dashboard
    └── result.html             # Legacy fallback results page
```

---

## ⚙️ Installation & Local Execution

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/your-username/Starbucks_Customer_Segmentation.git
cd Starbucks_Customer_Segmentation-main/Starbucks_Customer_Segmentation-main

# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Application
```bash
python app.py
```

Open your browser at:
```text
http://127.0.0.1:5000
```

---

## 🧠 Machine Learning Pipeline Details

### A. Preprocessing & Feature Engineering
* **Missing Value Imputation:** Customers with missing gender or income (represented by sentinel age `118`) are systematically filtered, retaining 14,825 verified profiles.
* **Feature Scaling:** All 7 segmentation features (`money_spent`, `num_transactions`, `num_received`, `num_viewed`, `num_completed`, `income`, `age`) are transformed via `StandardScaler` to ensure distance metrics are invariant to scale differences.

### B. Unsupervised Clustering
* **Algorithm:** `KMeans(n_clusters=5, random_state=42, n_init=15)`
* **Validation:** Optimal $k=5$ justified by the inflection point in the inertia curve and highest relative silhouette score.
* **Dimensionality Reduction:** 2-component Principal Component Analysis (`PCA`) maps high-dimensional points into a 2D coordinate space for visual inspection.

### C. Supervised Predictive Model
* **Algorithm:** `RandomForestClassifier(n_estimators=100, max_depth=12, min_samples_split=10)`
* **Target:** `was_completed` (binary completion of specific promotional offer).
* **Leakage Prevention:** Features strictly limited to pre-event customer attributes, historical metrics, and offer attributes. Post-event metrics (`viewed_time`, `completed_time`) are excluded.
* **Evaluation Metrics:**
  * **Accuracy:** `83.68%`
  * **Precision:** `79.14%`
  * **Recall:** `74.82%`
  * **F1-Score:** `76.92%`
  * **ROC-AUC Score:** `0.9027`

---

## 🔬 Dataset Limitations & Academic Nuance

1. **Informational Offers:** In the Starbucks dataset, informational offers do not register `offer completed` events (only `offer received` and `offer viewed`). The platform explicitly marks informational completion as "N/A" rather than zero to avoid misleading conversion statistics.
2. **Temporal Overlaps:** Customers frequently hold multiple concurrent offers. While transaction amounts are attributable to the active customer timeline, exact single-offer incrementality requires synthetic control group estimation.
3. **Observation Horizon:** Transactions are recorded over a simulated 30-day window (714 hours).

---

## 🎓 Suggested Future Enhancements (Final-Year Project Scope)

* **Uplift Modeling (Causal ML):** Implement Two-Model or X-Learner approaches to predict the *incremental* spend caused by an offer rather than just organic redemption.
* **Time-Series CLV Forecasting:** Integrate BG/NBD and Gamma-Gamma models to forecast customer lifetime value over 6-month horizons.
* **Real-Time Webhook Simulator:** Simulate live POS event ingestion via Kafka or Celery background task workers.

---

**Developed for Starbucks Promotional Campaign & Customer Intelligence Analytics.**

