"""
test_api_contracts.py — BharatPrice Pulse
FastAPI TestClient endpoint tests verifying API contracts, validation, and safe outputs.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "mock_mode" in data
    assert "version" in data


def test_quota_endpoint_security():
    response = client.get("/api/quota")
    assert response.status_code == 200
    data = response.json()
    # Ensure safe fields only — NO API KEY LEAKAGE
    assert "monthly_limit" in data
    assert "monthly_remaining" in data
    assert "api_key" not in data
    assert "key" not in data


def test_analyze_endpoint_mock_execution():
    payload = {
        "product_raw": "Fortune Mustard Oil 1L",
        "city_raw": "Jaipur",
        "selling_price": 175.0,
        "landed_cost": 142.0,
        "analysis_mode": "standard",
        "ui_language": "en"
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "analysis_id" in data
    assert "action" in data
    assert "action_label" in data
    assert "market_metrics" in data
    assert "fusion" in data
    assert "sources" in data
    assert data["mock_mode"] is True
    assert data["searches_consumed"] <= 4


def test_analyze_validation_errors():
    # Missing required field selling_price
    invalid_payload = {
        "product_raw": "Fortune Mustard Oil",
        "city_raw": "Jaipur",
    }
    response = client.post("/api/analyze", json=invalid_payload)
    assert response.status_code == 422

    # Negative price
    neg_payload = {
        "product_raw": "Fortune Mustard Oil",
        "city_raw": "Jaipur",
        "selling_price": -50.0,
    }
    response = client.post("/api/analyze", json=neg_payload)
    assert response.status_code == 422


def test_history_endpoint():
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_upload_image_invalid_content_type():
    # Test text file upload rejected cleanly
    response = client.post(
        "/api/upload-image",
        files={"file": ("test.txt", b"plain text", "text/plain")}
    )
    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()


def test_analyze_response_contains_rich_evidence_lists():
    payload = {
        "product_raw": "Samsung Galaxy M14 5G",
        "city_raw": "Delhi",
        "selling_price": 12499.0,
        "landed_cost": 11500.0,
        "analysis_mode": "standard",
        "ui_language": "en"
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "local_merchants" in data
    assert "news_articles" in data
    assert "finance_signals" in data
    assert "trends_evidence" in data
    assert isinstance(data["local_merchants"], list)
    assert isinstance(data["news_articles"], list)


def test_auth_login_and_user_scoped_history():
    # 1. Login user
    login_payload = {
        "email": "seller.ramesh@gmail.com",
        "name": "Ramesh Kumar",
        "provider": "google",
    }
    resp = client.post("/api/auth/login", json=login_payload)
    assert resp.status_code == 200
    auth_data = resp.json()
    assert auth_data["status"] == "authenticated"
    assert auth_data["user"]["email"] == "seller.ramesh@gmail.com"
    assert auth_data["user"]["name"] == "Ramesh Kumar"

    # 2. Check /api/auth/me
    me_resp = client.get("/api/auth/me?user_email=seller.ramesh@gmail.com")
    assert me_resp.status_code == 200
    assert me_resp.json()["authenticated"] is True
    assert me_resp.json()["user"]["email"] == "seller.ramesh@gmail.com"

    # 3. Analyze as Ramesh
    analysis_payload = {
        "product_raw": "Basmati Rice 5kg",
        "city_raw": "Delhi",
        "selling_price": 500.0,
        "user_email": "seller.ramesh@gmail.com",
        "description_raw": "1121 steam aged rice",
    }
    analyze_resp = client.post("/api/analyze", json=analysis_payload)
    assert analyze_resp.status_code == 200
    res_data = analyze_resp.json()
    assert res_data["user_email"] == "seller.ramesh@gmail.com"
    assert res_data["product_description"] is not None

    # 4. History scoped to Ramesh should return his analysis
    ramesh_hist = client.get("/api/history?user_email=seller.ramesh@gmail.com")
    assert ramesh_hist.status_code == 200
    items = ramesh_hist.json()["items"]
    assert len(items) >= 1
    assert any(i["user_email"] == "seller.ramesh@gmail.com" for i in items)

    # 5. History for another user should NOT contain Ramesh's item
    other_hist = client.get("/api/history?user_email=other.merchant@gmail.com")
    assert other_hist.status_code == 200
    other_items = other_hist.json()["items"]
    assert all(i["user_email"] == "other.merchant@gmail.com" for i in other_items)

