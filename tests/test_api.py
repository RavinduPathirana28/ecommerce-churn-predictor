import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_api_health():
    """Verify health endpoint returns status 200 and healthy flag."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data

def test_api_metadata():
    """Verify metadata endpoint returns expected schema and 33 features."""
    response = client.get("/api/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "feature_columns" in data
    assert len(data["feature_columns"]) == 33
    assert "metrics_test" in data

def test_api_presets():
    """Verify preset archetypes are returned and well-formed."""
    response = client.get("/api/presets")
    assert response.status_code == 200
    presets = response.json()
    assert isinstance(presets, list)
    assert len(presets) >= 3
    for p in presets:
        assert "id" in p
        assert "name" in p
        assert "data" in p

def test_api_customers():
    """Verify customer directory cohort returns calculated churn risks."""
    response = client.get("/api/customers")
    assert response.status_code == 200
    customers = response.json()
    assert isinstance(customers, list)
    assert len(customers) > 0
    for c in customers:
        assert "id" in c
        assert "churn_risk" in c
        assert "risk_tier" in c

def test_api_predict_valid_payload():
    """Verify predict endpoint handles valid input and outputs bounded probability."""
    payload = {
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
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["prediction"] in [0, 1]
    assert 0.0 <= result["churn_probability"] <= 1.0
    assert 0.0 <= result["churn_percentage"] <= 100.0
    assert result["features_evaluated"] == 33
    assert "risk_assessment" in result

def test_api_predict_validation_error():
    """Verify Pydantic input validation rejects out-of-bound inputs with 422."""
    # CityTier must be between 1 and 3; SatisfactionScore must be between 1 and 5
    invalid_payload = {
        "CityTier": 99,
        "SatisfactionScore": 10,
        "CashbackAmount": -50.0
    }
    response = client.post("/api/predict", json=invalid_payload)
    assert response.status_code == 422
