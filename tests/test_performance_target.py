from fastapi.testclient import TestClient
from app.performance_target import app


def test_health_endpoint_reports_service_status() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "testforge"}


def test_products_endpoint_returns_consistent_item_count() -> None:
    response = TestClient(app).get("/products")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 3
    assert len(payload["items"]) == payload["count"]
    assert [item["name"] for item in payload["items"]] == [
        "Backpack",
        "Bike Light",
        "T-Shirt",
    ]
