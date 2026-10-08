import pytest
import pandas as pd
from app import preprocess_customer, generate_insights_and_actions, CustomerInput, FEATURE_COLUMNS, RAW_MEDIANS

def test_preprocess_feature_columns_and_shape():
    """Verify preprocessed customer DataFrame matches the exact 33 model feature columns."""
    sample_input = CustomerInput(
        Tenure=12.0,
        CityTier=1,
        WarehouseToHome=15.0,
        HourSpendOnApp=3.0,
        NumberOfDeviceRegistered=3,
        SatisfactionScore=4,
        NumberOfAddress=2,
        Complain=0,
        OrderAmountHikeFromlastYear=15.0,
        CouponUsed=1.0,
        OrderCount=3.0,
        DaySinceLastOrder=5.0,
        CashbackAmount=180.0,
        Gender="Female",
        MaritalStatus="Married",
        PreferredLoginDevice="Mobile Phone",
        PreferredPaymentMode="Credit Card",
        PreferedOrderCat="Fashion"
    )
    df_transformed, context = preprocess_customer(sample_input)
    assert isinstance(df_transformed, pd.DataFrame)
    assert df_transformed.shape == (1, 33)
    assert list(df_transformed.columns) == FEATURE_COLUMNS

def test_preprocess_missing_indicators_and_median_imputation():
    """Verify missing values trigger MNAR indicator flags and receive training medians."""
    # Omit all optional fields
    sparse_input = CustomerInput(
        Tenure=None,
        WarehouseToHome=None,
        HourSpendOnApp=None,
        OrderAmountHikeFromlastYear=None,
        CouponUsed=None,
        OrderCount=None,
        DaySinceLastOrder=None,
        CityTier=2,
        NumberOfDeviceRegistered=2,
        SatisfactionScore=3,
        NumberOfAddress=1,
        Complain=0,
        CashbackAmount=160.0
    )
    df_transformed, context = preprocess_customer(sparse_input)
    row = df_transformed.iloc[0]

    # Verify missing indicators are flagged
    assert row["Tenure_was_missing"] == 1
    assert row["WarehouseToHome_was_missing"] == 1
    assert row["HourSpendOnApp_was_missing"] == 1
    assert row["OrderAmountHikeFromlastYear_was_missing"] == 1
    assert row["CouponUsed_was_missing"] == 1
    assert row["OrderCount_was_missing"] == 1

    # Verify imputed numeric values equal the training medians
    assert row["Tenure"] == RAW_MEDIANS.get("Tenure", 9.0)
    assert row["WarehouseToHome"] == RAW_MEDIANS.get("WarehouseToHome", 14.0)
    assert row["HourSpendOnApp"] == RAW_MEDIANS.get("HourSpendOnApp", 3.0)

def test_category_consolidation():
    """Verify categorical synonyms (e.g. Phone -> Mobile Phone, COD -> Cash on Delivery)."""
    synonym_input = CustomerInput(
        PreferredLoginDevice="Phone",
        PreferredPaymentMode="COD",
        PreferedOrderCat="Mobile",
        Tenure=10.0,
        CashbackAmount=160.0
    )
    df_transformed, context = preprocess_customer(synonym_input)
    row = df_transformed.iloc[0]

    assert row["PreferredLoginDevice_Mobile_Phone"] == 1
    assert row["PreferedOrderCat_Mobile_Phone"] == 1
    assert context["order_cat"] == "Mobile Phone"

def test_insights_and_actions_risk_tiers():
    """Verify risk tier classification and recommended actions."""
    # Critical risk (> 0.70) with complaint and new tenure
    crit_context = {
        'tenure': 1.0,
        'complain': 1,
        'cashback': 120.0,
        'days_since_order': 2.0,
        'order_count': 1.0,
        'wh_dist': 25.0,
        'marital_status': 'Single',
        'order_cat': 'Mobile Phone'
    }
    crit_insights = generate_insights_and_actions(0.85, crit_context)
    assert crit_insights["risk_level"] == "Critical Risk"
    assert crit_insights["badge_color"] == "red"
    assert len(crit_insights["risk_factors"]) > 0
    assert len(crit_insights["recommended_actions"]) > 0

    # Safe / Low risk (< 0.20) without risk flags
    safe_context = {
        'tenure': 24.0,
        'complain': 0,
        'cashback': 220.0,
        'days_since_order': 5.0,
        'order_count': 6.0,
        'wh_dist': 8.0,
        'marital_status': 'Married',
        'order_cat': 'Laptop & Accessory'
    }
    safe_insights = generate_insights_and_actions(0.05, safe_context)
    assert safe_insights["risk_level"] == "Low Risk"
    assert safe_insights["badge_color"] == "green"
