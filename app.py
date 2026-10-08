import os
import json
import joblib
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Initialize FastAPI App
app = FastAPI(
    title="E-Commerce Customer Churn Prediction System",
    description="IT3051 Fundamentals of Data Mining - Production Churn Decision Support Service",
    version="1.0.0"
)

# Enable CORS for local testing and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Model and Metadata
MODEL_PATH = "churn_model.joblib"
METADATA_PATH = "model_metadata.json"

if not os.path.exists(MODEL_PATH) or not os.path.exists(METADATA_PATH):
    raise RuntimeError("Model or metadata artifact not found! Run train_and_export.py first.")

model = joblib.load(MODEL_PATH)
with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

FEATURE_COLUMNS = metadata["feature_columns"]
RAW_MEDIANS = metadata.get("raw_medians", {})
CATEGORICAL_OPTIONS = metadata.get("categorical_options", {})
DEFAULTS = metadata.get("defaults", {})

# Pydantic Input Schema
class CustomerInput(BaseModel):
    Tenure: Optional[float] = Field(None, ge=0.0, le=60.0, description="Months since customer signup (0-60)")
    CityTier: int = Field(1, ge=1, le=3, description="City Tier (1, 2, or 3)")
    WarehouseToHome: Optional[float] = Field(None, ge=1.0, le=150.0, description="Distance from warehouse in km")
    HourSpendOnApp: Optional[float] = Field(None, ge=0.0, le=10.0, description="Average hours spent on mobile app per day")
    NumberOfDeviceRegistered: int = Field(3, ge=1, le=10, description="Total devices registered on account")
    SatisfactionScore: int = Field(3, ge=1, le=5, description="Customer satisfaction rating (1-5)")
    NumberOfAddress: int = Field(2, ge=1, le=25, description="Number of saved shipping addresses")
    Complain: int = Field(0, ge=0, le=1, description="Whether customer filed a complaint (0=No, 1=Yes)")
    OrderAmountHikeFromlastYear: Optional[float] = Field(None, ge=0.0, le=50.0, description="Percentage order amount hike from last year")
    CouponUsed: Optional[float] = Field(None, ge=0.0, le=30.0, description="Number of coupons used in the last month")
    OrderCount: Optional[float] = Field(None, ge=1.0, le=50.0, description="Total order count in the last month")
    DaySinceLastOrder: Optional[float] = Field(None, ge=0.0, le=60.0, description="Days elapsed since the customer's last order")
    CashbackAmount: float = Field(160.0, ge=0.0, le=500.0, description="Average cashback earned by customer")
    
    # Categorical fields
    Gender: str = Field("Female", description="Gender (Female, Male)")
    MaritalStatus: str = Field("Married", description="Marital status (Single, Married, Divorced)")
    PreferredLoginDevice: str = Field("Mobile Phone", description="Login device (Mobile Phone, Computer)")
    PreferredPaymentMode: str = Field("Debit Card", description="Payment mode (Debit Card, Credit Card, E-wallet, Cash on Delivery, UPI)")
    PreferedOrderCat: str = Field("Laptop & Accessory", description="Preferred order category (Laptop & Accessory, Mobile Phone, Fashion, Grocery, Others)")

def preprocess_customer(data: CustomerInput) -> pd.DataFrame:
    """Transform raw customer input into the exact 33 features used during model training."""
    raw_dict = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    
    # 1. Track missingness for columns identified as MNAR in Stage 3 & 4
    tenure_val = raw_dict['Tenure']
    tenure_was_missing = 1 if tenure_val is None or pd.isna(tenure_val) else 0
    wh_was_missing = 1 if raw_dict['WarehouseToHome'] is None or pd.isna(raw_dict['WarehouseToHome']) else 0
    app_was_missing = 1 if raw_dict['HourSpendOnApp'] is None or pd.isna(raw_dict['HourSpendOnApp']) else 0
    hike_was_missing = 1 if raw_dict['OrderAmountHikeFromlastYear'] is None or pd.isna(raw_dict['OrderAmountHikeFromlastYear']) else 0
    ordercount_was_missing = 1 if raw_dict['OrderCount'] is None or pd.isna(raw_dict['OrderCount']) else 0
    coupon_was_missing = 1 if raw_dict['CouponUsed'] is None or pd.isna(raw_dict['CouponUsed']) else 0

    # 2. Impute missing numeric fields with exact training medians
    tenure = RAW_MEDIANS.get('Tenure', 9.0) if tenure_was_missing else float(tenure_val)
    wh = RAW_MEDIANS.get('WarehouseToHome', 14.0) if wh_was_missing else float(raw_dict['WarehouseToHome'])
    app_hours = RAW_MEDIANS.get('HourSpendOnApp', 3.0) if app_was_missing else float(raw_dict['HourSpendOnApp'])
    hike = RAW_MEDIANS.get('OrderAmountHikeFromlastYear', 15.0) if hike_was_missing else float(raw_dict['OrderAmountHikeFromlastYear'])
    order_count = RAW_MEDIANS.get('OrderCount', 2.0) if ordercount_was_missing else float(raw_dict['OrderCount'])
    coupons = RAW_MEDIANS.get('CouponUsed', 1.0) if coupon_was_missing else float(raw_dict['CouponUsed'])
    days_since_order = RAW_MEDIANS.get('DaySinceLastOrder', 3.0) if raw_dict['DaySinceLastOrder'] is None else float(raw_dict['DaySinceLastOrder'])

    # 3. Category consolidation mapping (Stage 4 Step 4)
    login_device = raw_dict['PreferredLoginDevice']
    if login_device in ['Phone', 'Mobile Phone']:
        login_device = 'Mobile Phone'
    
    payment_mode = raw_dict['PreferredPaymentMode']
    if payment_mode in ['COD', 'Cash on Delivery']:
        payment_mode = 'Cash on Delivery'
    elif payment_mode in ['CC', 'Credit Card']:
        payment_mode = 'Credit Card'
        
    order_cat = raw_dict['PreferedOrderCat']
    if order_cat in ['Mobile', 'Mobile Phone']:
        order_cat = 'Mobile Phone'

    # 4. Engineered Tenure threshold features (Stage 7 Feature Engineering Experiment)
    tenure_new_0_3mo = 1 if tenure <= 3.0 else 0
    tenure_loyal_12mo = 1 if tenure > 12.0 else 0

    # 5. Populate feature dictionary matching exact FEATURE_COLUMNS
    feature_dict = {
        'Tenure': tenure,
        'CityTier': int(raw_dict['CityTier']),
        'WarehouseToHome': wh,
        'HourSpendOnApp': app_hours,
        'NumberOfDeviceRegistered': int(raw_dict['NumberOfDeviceRegistered']),
        'SatisfactionScore': int(raw_dict['SatisfactionScore']),
        'NumberOfAddress': int(raw_dict['NumberOfAddress']),
        'Complain': int(raw_dict['Complain']),
        'OrderAmountHikeFromlastYear': hike,
        'CouponUsed': coupons,
        'OrderCount': order_count,
        'DaySinceLastOrder': days_since_order,
        'CashbackAmount': float(raw_dict['CashbackAmount']),
        
        # Missing indicator features
        'Tenure_was_missing': tenure_was_missing,
        'WarehouseToHome_was_missing': wh_was_missing,
        'HourSpendOnApp_was_missing': app_was_missing,
        'OrderAmountHikeFromlastYear_was_missing': hike_was_missing,
        'OrderCount_was_missing': ordercount_was_missing,
        'CouponUsed_was_missing': coupon_was_missing,

        # One-hot encoded categorical dummies
        'Gender_Male': 1 if raw_dict['Gender'] == 'Male' else 0,
        'MaritalStatus_Married': 1 if raw_dict['MaritalStatus'] == 'Married' else 0,
        'MaritalStatus_Single': 1 if raw_dict['MaritalStatus'] == 'Single' else 0,
        'PreferredLoginDevice_Mobile_Phone': 1 if login_device == 'Mobile Phone' else 0,
        'PreferredPaymentMode_Credit_Card': 1 if payment_mode == 'Credit Card' else 0,
        'PreferredPaymentMode_Debit_Card': 1 if payment_mode == 'Debit Card' else 0,
        'PreferredPaymentMode_E_wallet': 1 if payment_mode == 'E-wallet' else 0,
        'PreferredPaymentMode_UPI': 1 if payment_mode == 'UPI' else 0,
        'PreferedOrderCat_Grocery': 1 if order_cat == 'Grocery' else 0,
        'PreferedOrderCat_Laptop_and_Accessory': 1 if order_cat == 'Laptop & Accessory' else 0,
        'PreferedOrderCat_Mobile_Phone': 1 if order_cat == 'Mobile Phone' else 0,
        'PreferedOrderCat_Others': 1 if order_cat == 'Others' else 0,

        # Tenure engineered flags
        'Tenure_New_0_3mo': tenure_new_0_3mo,
        'Tenure_Loyal_12mo_plus': tenure_loyal_12mo
    }

    # Verify column alignment
    df_transformed = pd.DataFrame([feature_dict])[FEATURE_COLUMNS]
    return df_transformed, {
        'tenure': tenure,
        'complain': raw_dict['Complain'],
        'cashback': raw_dict['CashbackAmount'],
        'days_since_order': days_since_order,
        'order_count': order_count,
        'wh_dist': wh,
        'marital_status': raw_dict['MaritalStatus'],
        'order_cat': order_cat
    }

BASELINE_CHURN = 16.8  # overall churn rate (%) in the E-Commerce Churn dataset

# Generate personalized retention insights and recommended actions based on customer risk.
def generate_insights_and_actions(prob: float, context: dict) -> Dict[str, Any]:
    """Flag segment-level risk signals and suggest retention actions.

    Note: these signals are rule-based, using churn rates observed in the training
    dataset (EDA). They explain *which segments* the customer falls into; they are
    not per-prediction model attributions (e.g. SHAP values).
    """
    risk_factors = []
    actions = []

    # Tenure: 41.9% churn for tenure <= 3 months vs 5.6% afterwards
    if context['tenure'] <= 3:
        risk_factors.append({
            "factor": "New customer (tenure ≤ 3 months)",
            "severity": "High",
            "segment_rate": 41.9,
            "description": "Customers in their first 3 months churn at 41.9%, versus 5.6% for longer-tenured customers."
        })
        actions.append({
            "action": "Early-life onboarding journey",
            "detail": "Enroll in a welcome series with milestone rewards on the 2nd and 3rd orders.",
            "owner": "Lifecycle Marketing",
            "priority": "P1"
        })

    # Complaint: 31.7% churn with complaint vs 10.9% without
    if context['complain'] == 1:
        risk_factors.append({
            "factor": "Open complaint on record",
            "severity": "High",
            "segment_rate": 31.7,
            "description": "Customers with a complaint churn at 31.7%, about 2.9× the 10.9% rate of those without."
        })
        actions.append({
            "action": "Priority service recovery call",
            "detail": "Escalate the ticket to a senior agent and close the loop within 24 hours.",
            "owner": "Customer Support",
            "priority": "P1"
        })

    # Marital status: single 26.7% vs married 11.5%
    if context['marital_status'] == 'Single':
        risk_factors.append({
            "factor": "Single customer segment",
            "severity": "Medium",
            "segment_rate": 26.7,
            "description": "Single customers churn at 26.7%, versus 11.5% for married customers."
        })
        actions.append({
            "action": "Personalised recommendations",
            "detail": "Target with individual-focused bundles in their preferred category.",
            "owner": "CRM",
            "priority": "P3"
        })

    # Cashback: 27.3% churn below $140 vs 14.4% at/above
    if context['cashback'] < 140:
        risk_factors.append({
            "factor": "Low cashback earned (< $140)",
            "severity": "Medium",
            "segment_rate": 27.3,
            "description": f"Cashback of ${context['cashback']:.0f} is below the $163 median; this segment churns at 27.3% vs 14.4%."
        })
        actions.append({
            "action": "Targeted cashback boost",
            "detail": "Offer boosted cashback on the next two orders in their top category.",
            "owner": "Loyalty Team",
            "priority": "P2"
        })

    # Warehouse distance: 20.4% churn above 20 km vs 14.6%
    if context['wh_dist'] > 20:
        risk_factors.append({
            "factor": "Long delivery distance (> 20 km)",
            "severity": "Low",
            "segment_rate": 20.4,
            "description": "Customers more than 20 km from the warehouse churn at 20.4%, versus 14.6% for closer customers."
        })
        actions.append({
            "action": "Free express shipping",
            "detail": "Upgrade delivery on the next order to offset longer transit times.",
            "owner": "Logistics",
            "priority": "P3"
        })

    # Fallback if no segment flags
    if not risk_factors:
        actions.append({
            "action": "Maintain engagement",
            "detail": "Include in standard loyalty programme; no targeted intervention needed.",
            "owner": "CRM",
            "priority": "P4"
        })

    # Classify overall risk level
    if prob >= 0.70:
        risk_level = "Critical Risk"
        badge_color = "red"
        summary = "Very likely to churn. Prioritise for retention outreach this week."
    elif prob >= 0.40:
        risk_level = "High Risk"
        badge_color = "orange"
        summary = "More likely than not to be at risk. Proactive outreach recommended."
    elif prob >= 0.20:
        risk_level = "Moderate Risk"
        badge_color = "yellow"
        summary = "Above-average risk. Monitor and include in targeted campaigns."
    else:
        risk_level = "Low Risk"
        badge_color = "green"
        summary = "The model expects this customer to stay. No urgent action needed."

    return {
        "risk_level": risk_level,
        "badge_color": badge_color,
        "summary": summary,
        "baseline_churn": BASELINE_CHURN,
        "risk_factors": risk_factors,
        "recommended_actions": actions
    }

# API Endpoints
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "E-Commerce Churn Prediction System",
        "stage": "Stage 9: Backend Functional Service",
        "model": metadata.get("model_name", "Tuned Gradient Boosting")
    }

@app.get("/api/metadata")
def get_metadata():
    return metadata

@app.post("/api/predict")
def predict_churn(customer: CustomerInput):
    try:
        df_transformed, context = preprocess_customer(customer)
        churn_prob = float(model.predict_proba(df_transformed)[0][1])
        prediction = int(model.predict(df_transformed)[0])
        
        insights = generate_insights_and_actions(churn_prob, context)
        
        return {
            "prediction": prediction,
            "prediction_label": "Churned" if prediction == 1 else "Retained",
            "churn_probability": round(churn_prob, 4),
            "churn_percentage": round(churn_prob * 100, 2),
            "risk_assessment": insights,
            "features_evaluated": len(FEATURE_COLUMNS)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/api/predict/batch")
def predict_batch(customers: List[CustomerInput]):
    """Score multiple customer records concurrently in a single vectorized batch."""
    if not customers:
        raise HTTPException(status_code=400, detail="Customer list cannot be empty.")
    if len(customers) > 500:
        raise HTTPException(status_code=400, detail="Batch size exceeds maximum limit of 500 records.")

    try:
        dfs = []
        contexts = []
        for c in customers:
            df_t, ctx = preprocess_customer(c)
            dfs.append(df_t)
            contexts.append(ctx)

        df_batch = pd.concat(dfs, ignore_index=True)
        probabilities = model.predict_proba(df_batch)[:, 1]
        predictions = model.predict(df_batch)

        results = []
        tier_counts = {"Critical Risk": 0, "High Risk": 0, "Moderate Risk": 0, "Low Risk": 0}

        for i, (prob, pred, ctx) in enumerate(zip(probabilities, predictions, contexts)):
            prob_float = float(prob)
            insights = generate_insights_and_actions(prob_float, ctx)
            tier = insights["risk_level"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

            results.append({
                "record_index": i,
                "prediction": int(pred),
                "prediction_label": "Churned" if pred == 1 else "Retained",
                "churn_probability": round(prob_float, 4),
                "churn_percentage": round(prob_float * 100, 2),
                "risk_level": tier,
                "badge_color": insights["badge_color"],
                "summary": insights["summary"],
                "top_risk_factors": [rf["factor"] for rf in insights["risk_factors"][:2]],
                "priority_action": insights["recommended_actions"][0]["action"] if insights["recommended_actions"] else "None"
            })

        return {
            "total_processed": len(results),
            "tier_breakdown": tier_counts,
            "predictions": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")

@app.get("/api/presets")
def get_presets():
    """Return privacy-compliant test personas for evaluation demonstrations."""
    return [
        {
            "id": "new_churn_risk",
            "name": "🚨 Critical Risk Cohort (Account #9428)",
            "description": "1 month tenure, unresolved complaint, low cashback, single",
            "data": {
                "Tenure": 1.0,
                "CityTier": 3,
                "WarehouseToHome": 25.0,
                "HourSpendOnApp": 2.0,
                "NumberOfDeviceRegistered": 4,
                "SatisfactionScore": 5,
                "NumberOfAddress": 5,
                "Complain": 1,
                "OrderAmountHikeFromlastYear": 11.0,
                "CouponUsed": 0.0,
                "OrderCount": 1.0,
                "DaySinceLastOrder": 2.0,
                "CashbackAmount": 120.0,
                "Gender": "Female",
                "MaritalStatus": "Single",
                "PreferredLoginDevice": "Mobile Phone",
                "PreferredPaymentMode": "Cash on Delivery",
                "PreferedOrderCat": "Mobile Phone"
            }
        },
        {
            "id": "loyal_vip",
            "name": "⭐ Loyal VIP Cohort (Account #3051)",
            "description": "24 months tenure, zero complaints, high cashback, frequent orders",
            "data": {
                "Tenure": 24.0,
                "CityTier": 1,
                "WarehouseToHome": 8.0,
                "HourSpendOnApp": 3.0,
                "NumberOfDeviceRegistered": 3,
                "SatisfactionScore": 4,
                "NumberOfAddress": 2,
                "Complain": 0,
                "OrderAmountHikeFromlastYear": 19.0,
                "CouponUsed": 3.0,
                "OrderCount": 6.0,
                "DaySinceLastOrder": 7.0,
                "CashbackAmount": 245.0,
                "Gender": "Male",
                "MaritalStatus": "Married",
                "PreferredLoginDevice": "Computer",
                "PreferredPaymentMode": "Credit Card",
                "PreferedOrderCat": "Laptop & Accessory"
            }
        },
        {
            "id": "moderate_watch",
            "name": "⚠️ Watchlist Cohort (Account #8104)",
            "description": "5 months tenure, moderate warehouse distance, moderate satisfaction",
            "data": {
                "Tenure": 5.0,
                "CityTier": 2,
                "WarehouseToHome": 20.0,
                "HourSpendOnApp": 2.0,
                "NumberOfDeviceRegistered": 3,
                "SatisfactionScore": 3,
                "NumberOfAddress": 3,
                "Complain": 1,
                "OrderAmountHikeFromlastYear": 12.0,
                "CouponUsed": 1.0,
                "OrderCount": 2.0,
                "DaySinceLastOrder": 10.0,
                "CashbackAmount": 160.0,
                "Gender": "Female",
                "MaritalStatus": "Single",
                "PreferredLoginDevice": "Mobile Phone",
                "PreferredPaymentMode": "Debit Card",
                "PreferedOrderCat": "Fashion"
            }
        }
    ]

@app.get("/api/customers")
def get_customers():
    """Return a realistic, privacy-compliant cohort of e-commerce customers without PII,
    dynamically evaluated against the model for 100% mathematical consistency."""
    customers = [
        {
            "id": "CUST-9428",
            "name": "Account #9428",
            "account_ref": "ACC-9428-T3",
            "avatar": "#94",
            "segment": "Tier 3 Regional",
            "ltv": "$380",
            "tenure_months": 1,
            "orders": 1,
            "complaint": 1,
            "data": {
                "Tenure": 1.0, "CityTier": 3, "WarehouseToHome": 25.0, "HourSpendOnApp": 2.0,
                "NumberOfDeviceRegistered": 4, "SatisfactionScore": 5, "NumberOfAddress": 5,
                "Complain": 1, "OrderAmountHikeFromlastYear": 11.0, "CouponUsed": 0.0,
                "OrderCount": 1.0, "DaySinceLastOrder": 2.0, "CashbackAmount": 120.0,
                "Gender": "Female", "MaritalStatus": "Single", "PreferredLoginDevice": "Mobile Phone",
                "PreferredPaymentMode": "Cash on Delivery", "PreferedOrderCat": "Mobile Phone"
            }
        },
        {
            "id": "CUST-8104",
            "name": "Account #8104",
            "account_ref": "ACC-8104-T2",
            "avatar": "#81",
            "segment": "Tier 2 Urban",
            "ltv": "$1,150",
            "tenure_months": 5,
            "orders": 2,
            "complaint": 1,
            "data": {
                "Tenure": 5.0, "CityTier": 2, "WarehouseToHome": 20.0, "HourSpendOnApp": 2.0,
                "NumberOfDeviceRegistered": 3, "SatisfactionScore": 3, "NumberOfAddress": 3,
                "Complain": 1, "OrderAmountHikeFromlastYear": 12.0, "CouponUsed": 1.0,
                "OrderCount": 2.0, "DaySinceLastOrder": 10.0, "CashbackAmount": 160.0,
                "Gender": "Female", "MaritalStatus": "Single", "PreferredLoginDevice": "Mobile Phone",
                "PreferredPaymentMode": "Debit Card", "PreferedOrderCat": "Fashion"
            }
        },
        {
            "id": "CUST-3051",
            "name": "Account #3051",
            "account_ref": "ACC-3051-VIP",
            "avatar": "#30",
            "segment": "Tier 1 Metro (VIP)",
            "ltv": "$4,290",
            "tenure_months": 24,
            "orders": 6,
            "complaint": 0,
            "data": {
                "Tenure": 24.0, "CityTier": 1, "WarehouseToHome": 8.0, "HourSpendOnApp": 3.0,
                "NumberOfDeviceRegistered": 3, "SatisfactionScore": 4, "NumberOfAddress": 2,
                "Complain": 0, "OrderAmountHikeFromlastYear": 19.0, "CouponUsed": 3.0,
                "OrderCount": 6.0, "DaySinceLastOrder": 7.0, "CashbackAmount": 245.0,
                "Gender": "Male", "MaritalStatus": "Married", "PreferredLoginDevice": "Computer",
                "PreferredPaymentMode": "Credit Card", "PreferedOrderCat": "Laptop & Accessory"
            }
        },
        {
            "id": "CUST-5219",
            "name": "Account #5219",
            "account_ref": "ACC-5219-T3",
            "avatar": "#52",
            "segment": "Tier 3 Regional",
            "ltv": "$590",
            "tenure_months": 1,
            "orders": 1,
            "complaint": 1,
            "data": {
                "Tenure": 1.0, "CityTier": 3, "WarehouseToHome": 16.0, "HourSpendOnApp": 2.0,
                "NumberOfDeviceRegistered": 4, "SatisfactionScore": 2, "NumberOfAddress": 3,
                "Complain": 1, "OrderAmountHikeFromlastYear": 13.0, "CouponUsed": 0.0,
                "OrderCount": 1.0, "DaySinceLastOrder": 14.0, "CashbackAmount": 160.0,
                "Gender": "Female", "MaritalStatus": "Single", "PreferredLoginDevice": "Mobile Phone",
                "PreferredPaymentMode": "Debit Card", "PreferedOrderCat": "Fashion"
            }
        },
        {
            "id": "CUST-6743",
            "name": "Account #6743",
            "account_ref": "ACC-6743-T2",
            "avatar": "#67",
            "segment": "Tier 2 Urban",
            "ltv": "$1,820",
            "tenure_months": 11,
            "orders": 4,
            "complaint": 0,
            "data": {
                "Tenure": 11.0, "CityTier": 2, "WarehouseToHome": 10.0, "HourSpendOnApp": 3.0,
                "NumberOfDeviceRegistered": 3, "SatisfactionScore": 4, "NumberOfAddress": 2,
                "Complain": 0, "OrderAmountHikeFromlastYear": 16.0, "CouponUsed": 2.0,
                "OrderCount": 4.0, "DaySinceLastOrder": 5.0, "CashbackAmount": 185.0,
                "Gender": "Male", "MaritalStatus": "Married", "PreferredLoginDevice": "Computer",
                "PreferredPaymentMode": "Debit Card", "PreferedOrderCat": "Grocery"
            }
        },
        {
            "id": "CUST-7890",
            "name": "Account #7890",
            "account_ref": "ACC-7890-T3",
            "avatar": "#78",
            "segment": "Tier 3 Regional",
            "ltv": "$740",
            "tenure_months": 1,
            "orders": 2,
            "complaint": 0,
            "data": {
                "Tenure": 1.0, "CityTier": 3, "WarehouseToHome": 24.0, "HourSpendOnApp": 3.0,
                "NumberOfDeviceRegistered": 4, "SatisfactionScore": 3, "NumberOfAddress": 4,
                "Complain": 0, "OrderAmountHikeFromlastYear": 12.0, "CouponUsed": 1.0,
                "OrderCount": 2.0, "DaySinceLastOrder": 9.0, "CashbackAmount": 160.0,
                "Gender": "Female", "MaritalStatus": "Single", "PreferredLoginDevice": "Mobile Phone",
                "PreferredPaymentMode": "Cash on Delivery", "PreferedOrderCat": "Mobile Phone"
            }
        },
        {
            "id": "CUST-4412",
            "name": "Account #4412",
            "account_ref": "ACC-4412-T1",
            "avatar": "#44",
            "segment": "Tier 1 Metro",
            "ltv": "$2,980",
            "tenure_months": 16,
            "orders": 5,
            "complaint": 0,
            "data": {
                "Tenure": 16.0, "CityTier": 1, "WarehouseToHome": 9.0, "HourSpendOnApp": 4.0,
                "NumberOfDeviceRegistered": 3, "SatisfactionScore": 5, "NumberOfAddress": 2,
                "Complain": 0, "OrderAmountHikeFromlastYear": 18.0, "CouponUsed": 2.0,
                "OrderCount": 5.0, "DaySinceLastOrder": 4.0, "CashbackAmount": 215.0,
                "Gender": "Male", "MaritalStatus": "Married", "PreferredLoginDevice": "Mobile Phone",
                "PreferredPaymentMode": "Credit Card", "PreferedOrderCat": "Laptop & Accessory"
            }
        },
        {
            "id": "CUST-9021",
            "name": "Account #9021",
            "account_ref": "ACC-9021-T3",
            "avatar": "#90",
            "segment": "Tier 3 Regional",
            "ltv": "$310",
            "tenure_months": 1,
            "orders": 1,
            "complaint": 1,
            "data": {
                "Tenure": 1.0, "CityTier": 3, "WarehouseToHome": 31.0, "HourSpendOnApp": 2.0,
                "NumberOfDeviceRegistered": 5, "SatisfactionScore": 2, "NumberOfAddress": 6,
                "Complain": 1, "OrderAmountHikeFromlastYear": 11.0, "CouponUsed": 0.0,
                "OrderCount": 1.0, "DaySinceLastOrder": 1.0, "CashbackAmount": 115.0,
                "Gender": "Female", "MaritalStatus": "Single", "PreferredLoginDevice": "Mobile Phone",
                "PreferredPaymentMode": "Cash on Delivery", "PreferedOrderCat": "Others"
            }
        }
    ]

    # Evaluate exact probabilities from model
    for c in customers:
        try:
            customer_data = c.get("data")
            if isinstance(customer_data, dict):
                inp = CustomerInput.model_validate(customer_data)
            else:
                inp = CustomerInput()
            df_t, _ = preprocess_customer(inp)
            prob = float(model.predict_proba(df_t)[0][1])
            c["churn_risk"] = round(prob * 100, 1)
            if prob >= 0.70:
                c["risk_tier"] = "Critical Risk"
                c["tier_badge"] = "badge-crit"
                c["avatar_color"] = "av-red"
            elif prob >= 0.40:
                c["risk_tier"] = "High Risk"
                c["tier_badge"] = "badge-crit"
                c["avatar_color"] = "av-red"
            elif prob >= 0.20:
                c["risk_tier"] = "Moderate Risk"
                c["tier_badge"] = "badge-mod"
                c["avatar_color"] = "av-amber"
            else:
                c["risk_tier"] = "Loyal Safe"
                c["tier_badge"] = "badge-safe"
                c["avatar_color"] = "av-green"
        except Exception:
            c["churn_risk"] = 0.0
            c["risk_tier"] = "Loyal Safe"
            c["tier_badge"] = "badge-safe"
            c["avatar_color"] = "av-green"

    return customers

# Favicon handler
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav_path = os.path.join(os.path.dirname(__file__), "static", "favicon.svg")
    if os.path.exists(fav_path):
        return FileResponse(fav_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404)

# Mount static folder for frontend (Stage 10)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting E-Commerce Churn Prediction Service on http://127.0.0.1:{port} ...")
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=False)
