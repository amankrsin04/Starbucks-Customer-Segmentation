# ☕ Starbucks Customer Offer Recommendation System

A Flask-based web application that uses **K-Means Clustering** to segment Starbucks customers based on their purchasing and offer engagement behavior, then recommends a suitable offer.

## 🚀 Live Demo
(https://starbucks-customer-segmentation.vercel.app)

## ✨ Features

* Customer behavior-based segmentation
* K-Means clustering with 5 customer segments
* Offer recommendation using Starbucks offer data
* Simple and user-friendly web interface
* Flask backend with HTML & CSS frontend

## 🧠 How It Works

1. Customer enters their behavior details.
2. The backend processes the customer data.
3. K-Means assigns the customer to a segment.
4. An offer is selected based on the segment.
5. The recommended offer and customer segment are displayed.

## 🛠️ Technologies

**Python • Flask • Pandas • NumPy • Scikit-learn • HTML • CSS**

## 📂 Project Structure

```text
Starbucks_Offer_Recommendation_Project/
│
├── app.py
├── requirements.txt
├── Starbucks_Customer_Segmentation.ipynb
│
├── data/
│   ├── profile(1).csv
│   ├── portfolio(1).csv
│   └── transcript(1).csv
│
├── templates/
│   ├── index.html
│   └── result.html
│
└── static/
    └── style.css
```

## ▶️ Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## 📌 Project Note

This project follows a simplified **college-level K-Means implementation** using customer behavior variables such as offers received, viewed, completed, transactions, and money spent. The final offer recommendation uses a simple rule-based strategy.

---

**Developed as a college project for Starbucks Customer Segmentation & Offer Recommendation.**
