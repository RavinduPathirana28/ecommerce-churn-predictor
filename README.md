#  ChurnGuard AI &bull; Enterprise Customer Retention Intelligence Platform

> **IT3051 Fundamentals of Data Mining — Mini Project (Stages 1–10)**  
> Production-grade E-Commerce Customer Churn Prediction and Decision Support System powered by **Tuned Gradient Boosting**.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3%2B-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![F1-Score](https://img.shields.io/badge/5--Fold%20CV%20F1-85.97%25-success)](#stage-6--7-model-performance)
[![ROC-AUC](https://img.shields.io/badge/Held--Out%20Test%20AUC-0.9992-brightgreen)](#stage-6--7-model-performance)

---

## Executive Summary

Customer churn is a silent growth killer for modern e-commerce platforms. Across our benchmark dataset of **5,630 e-commerce customers**, the baseline attrition rate is **16.8%**. Generic store-wide discounting is often ineffective—it gives away margins to customers who were never likely to leave while failing to target those who are genuinely at risk.

**ChurnGuard AI** is a production-ready machine learning service and interactive decision-support application designed to identify at-risk customers and support targeted retention strategies. At its core, it uses a **Tuned Gradient Boosting Classifier** that achieves an **85.97% 5-fold cross-validation F1-score** and **81.93% recall**, successfully identifying more than 8 out of 10 customers who are likely to churn. This enables businesses to move from reactive retention to proactive, data-driven customer engagement.

---

## Key Web Application Features

1. **Retention Predictor & Simulator (Tab 1)**:
   - **Real-time Speedometer Gauge**: Semicircular SVG dial with dynamic gradient track, animated needle, 4-tier risk threshold strip, and live risk percentage.
   - **Sample Profile Switcher**: 1-click loading of realistic archetypes (*Account #9428* `Critical Risk 99%`, *Account #8104* `Watchlist 28%`, *Account #3051* `Loyal Safe 3%`, and *Custom Account*).
   - **Interactive "What-If" Interventions**: Live scenario testing (e.g. closing an open complaint ticket, upgrading cashback to $220, or simulating 6-month loyalty) with immediate visual risk drop feedback.
   - **Attributed Segment Risk Signals**: Comparative risk driver bars benchmarked against platform averages.
   - **Prescriptive Retention Playbook**: Concrete retention tasks with priority badges (`P1`, `P2`, `P3`) and assigned business departments (*Support*, *CRM*, *Loyalty*, *Logistics*).

2. **Customer Directory Cohort Explorer (Tab 2)**:
   - **Enterprise Privacy & PII Masking**: Customer identities are strictly protected with pseudonymized identifiers (`Account #9428`, `ACC-9428-T3`) and numeric badge avatars, removing all names and personal email addresses.
   - Interactive monitoring table of active customer accounts with Customer IDs, LTV, tenure, order cadence, complaint status, and live model risk scores.
   - Real-time search filter by pseudonymized account ID, reference, or geographic segment.
   - 1-click **"Assess & Retain"** buttons that immediately load any customer profile into the predictor.

3. **Financial Retention ROI Simulator (Tab 3)**:
   - Executive business case calculator translating statistical metrics into financial ROI.
   - Configurable customer base, annual LTV, intervention success rate, and voucher cost.
   - Live revenue calculation modeling net annual revenue protected ($250,000+) and campaign ROI (1,000%+).

4. **Model Architecture & Academic Audit (Tab 4)**:
   - Full Multi-Algorithm Benchmark Comparison Table from Stage 6.
   - Top 10 Feature Importances visualization.
   - Complete technical notes on MNAR missingness handling, category consolidation, and feature engineering.

---

##  Stage 6 & 7: Model Performance & Benchmarking

All candidate algorithms were evaluated using **Stratified 5-Fold Cross-Validation** on the 5,630-record dataset:

| Model Architecture | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** (Baseline + SMOTE) | 82.33% | 48.52% | 81.27% | 60.70% | 0.9013 | Baseline Linear |
| **Decision Tree Classifier** (Baseline + SMOTE) | 88.26% | 63.63% | 70.72% | 66.91% | 0.8126 | Tree Baseline |
| **Random Forest** (Baseline Bagging) | 94.94% | 94.48% | 74.28% | 83.03% | 0.9769 | Ensemble Bagging |
| **Gradient Boosting** (Baseline Boosting) | 89.41% | 67.54% | 71.37% | 69.34% | 0.9148 | Default Params |
| **Tuned Random Forest** (RandomizedSearchCV) | 95.03% | 94.81% | 74.54% | 83.38% | 0.9781 | Tuned Runner-Up |
| **⭐ Tuned Gradient Boosting** *(Best model)* | **95.51%** | **90.56%** | **81.93%** | **85.97%** | **0.9729** | **Selected Champion** |

> **Held-Out Test Set Performance**: **ROC-AUC = 0.9992** | **Test F1 = 89.84%** | **Test Recall = 83.42%**

---

## 🔬 Key Data Mining Insights & Pipeline Design

1. **Missing Not At Random (MNAR) Tracking (Stage 3 & 4)**:
   - EDA revealed missingness in `Tenure`, `WarehouseToHome`, and `OrderCount` strongly correlated with churn propensity.
   - Retained missingness signal by generating 6 binary indicator flags (e.g. `Tenure_was_missing`) combined with training median imputation.
2. **Category Consolidation (Stage 4)**:
   - Cleaned typographical synonym duplicates (`Phone` &rarr; `Mobile Phone`, `CC` &rarr; `Credit Card`, `COD` &rarr; `Cash on Delivery`).
3. **Engineered Onboarding Cliff Flags (Stage 7)**:
   - Created `Tenure_New_0_3mo` and `Tenure_Loyal_12mo_plus`.
   - Data confirms customers in months 0–3 churn at **41.9%** (accounting for 68.9% of all platform churn) versus just **5.6%** thereafter.
4. **Class Imbalance Strategy (Stage 5)**:
   - Evaluated SMOTE oversampling versus tree class weighting; class weighting and probability calibration in Gradient Boosting avoided synthetic point distortion.

---

##  Tech Stack

- **Backend & ML Serving**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Scikit-Learn, Pandas, NumPy, Joblib
- **Frontend**: Vanilla HTML5, Modern CSS3 (Dark Theme Design System), Vanilla JavaScript (ES6+)
- **Model Pipeline**: Serialized 33-feature `churn_model.joblib` + metadata signature

---

##  Local Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/churnguard-ai.git
cd churnguard-ai
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Retrain or Verify Model Artifact
```bash
python train_and_export.py
```

### 5. Launch the Web Application
```bash
python app.py
```

Open your browser at:  
 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

Interactive API Swagger documentation is available at:  
 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

##  Repository Structure

```text
├── app.py                             # FastAPI backend & inference engine (Stage 9)
├── train_and_export.py                # Standalone training & pipeline serialization script
├── churn_model.joblib                 # Serialized Tuned Gradient Boosting champion pipeline
├── model_metadata.json                # Feature names, training medians & benchmark metrics
├── E-Commerce Churn Data.csv          # Raw 5,630-record benchmark dataset
├── FDM_E_commerce_churn_predictor.ipynb # Complete 8-stage data mining research notebook
├── requirements.txt                   # Production Python package requirements
├── Procfile                           # Cloud PaaS deployment configuration (Render/Railway)
├── .gitignore                         # Git exclusion rules
├── static/
│   ├── index.html                     # Enterprise multi-tab web application (Stage 10)
│   ├── style.css                      # Modern dark SaaS design system (no framework dependencies)
│   └── app.js                         # Dynamic state management, gauge math & API integration
└── README.md                          # Comprehensive project documentation
```

---

##  API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Web application UI frontend |
| `POST` | `/api/predict` | Live churn probability inference & prescriptive playbook |
| `GET` | `/api/customers` | Monitored customer cohort directory |
| `GET` | `/api/presets` | Quick-select demo customer profiles |
| `GET` | `/api/metadata` | Model specs, benchmark metrics & feature importances |
| `GET` | `/api/health` | Service health status |

---

##  Academic Coursework Reference

- **Module**: IT3051 Fundamentals of Data Mining
- **Project**: Customer Churn Prediction in E-Commerce
- **Submission Date**: October 2026
- **Champion Algorithm**: Tuned Gradient Boosting Classifier
