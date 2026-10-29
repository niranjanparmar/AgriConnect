from decimal import Decimal
from datetime import date
import pytest
from app.extensions import db
from app.models.user import User
from app.models.price import Crop, Market, CropPriceRecord, PriceAlert
from app.services.price_sync import PriceSyncService


def test_price_sync_service_benchmark_ingestion(app):
    """Verify standard benchmark dataset ingestion into database."""
    with app.app_context():
        service = PriceSyncService()
        results = service.sync(source="demo")

        assert results["status"] == "success"
        assert results["created"] > 0
        assert results["invalid_records"] == 0
        assert "Benchmark" in results["source"]

        # Verify records exist in database
        records = CropPriceRecord.query.all()
        assert len(records) >= results["created"]


def test_price_sync_service_idempotency(app):
    """Verify that syncing the same records repeatedly produces zero duplicate entries."""
    with app.app_context():
        service = PriceSyncService()
        initial = service.sync(source="demo")
        initial_count = CropPriceRecord.query.count()

        # Run exact same sync again
        repeat = service.sync(source="demo")
        repeat_count = CropPriceRecord.query.count()

        assert repeat["status"] == "success"
        assert repeat["created"] == 0
        assert repeat["skipped_duplicates"] == repeat["total_raw"]
        assert repeat_count == initial_count


def test_price_sync_service_validation_malformed_records(app):
    """Verify validation logic skips malformed, negative, or mathematically inverted records."""
    with app.app_context():
        service = PriceSyncService()

        malformed_batch = [
            # 1. Missing commodity
            {"state": "Gujarat", "market": "Rajkot APMC", "commodity": "", "arrival_date": "2026-10-29", "min_price": "2500", "max_price": "2900", "modal_price": "2700"},
            # 2. Negative price
            {"state": "Gujarat", "market": "Rajkot APMC", "commodity": "Mustard", "arrival_date": "2026-10-29", "min_price": "-100", "max_price": "2900", "modal_price": "2700"},
            # 3. Max < Min
            {"state": "Gujarat", "market": "Rajkot APMC", "commodity": "Barley", "arrival_date": "2026-10-29", "min_price": "3000", "max_price": "2000", "modal_price": "2500"},
            # 4. Modal outside bounds (modal > max)
            {"state": "Gujarat", "market": "Rajkot APMC", "commodity": "Millet", "arrival_date": "2026-10-29", "min_price": "2000", "max_price": "3000", "modal_price": "3500"},
            # 5. Invalid date string
            {"state": "Gujarat", "market": "Rajkot APMC", "commodity": "Gram", "arrival_date": "invalid-date", "min_price": "2000", "max_price": "3000", "modal_price": "2500"},
            # 6. Valid record in the same batch
            {"state": "Gujarat", "district": "Rajkot", "market": "Gondal APMC", "commodity": "Valid Sesame Seed", "variety": "White", "arrival_date": "2026-10-29", "min_price": "9000", "max_price": "11000", "modal_price": "10000"},
        ]

        results = service.sync_records(malformed_batch, "Test Batch")

        assert results["invalid_records"] == 5
        assert len(results["errors"]) == 5
        assert results["created"] == 1

        valid_rec = CropPriceRecord.query.join(CropPriceRecord.crop).filter(Crop.name == "Valid Sesame Seed").first()
        assert valid_rec is not None
        assert valid_rec.modal_price == Decimal("10000.00")


def test_price_sync_live_fallback_on_unconfigured_api(app):
    """Verify that auto mode safely falls back to benchmark data when AGRI_PRICE_API_KEY is unset."""
    with app.app_context():
        service = PriceSyncService(api_key="")
        results = service.sync(source="auto")

        assert results["status"] == "success"
        assert results["created"] > 0
        assert "Benchmark" in results["source"]


def test_price_alert_matching_on_sync(app, consumer_user):
    """Verify price sync triggers active user alerts when modal price crosses threshold."""
    with app.app_context():
        user = db.session.get(User, consumer_user.id)
        crop = Crop.query.filter_by(name="Wheat (Lokwan)").first()
        if not crop:
            crop = Crop(name="Wheat (Lokwan)")
            db.session.add(crop)
            db.session.flush()

        market = Market.query.filter_by(name="Rajkot APMC").first()
        if not market:
            market = Market(name="Rajkot APMC", district="Rajkot", state="Gujarat")
            db.session.add(market)
            db.session.flush()

        # User wants to be notified if Wheat rises Above ₹2700
        alert = PriceAlert(
            user_id=user.id,
            crop_id=crop.id,
            market_id=market.id,
            condition="Above",
            target_price=Decimal("2700.00"),
            is_active=True,
        )
        db.session.add(alert)
        db.session.commit()

        # Ingest record with modal price ₹2780
        test_data = [{
            "state": "Gujarat",
            "district": "Rajkot",
            "market": "Rajkot APMC",
            "commodity": "Wheat (Lokwan)",
            "variety": "Lokwan",
            "arrival_date": "2026-10-31",
            "min_price": "2600.00",
            "max_price": "2950.00",
            "modal_price": "2780.00",
            "arrivals_tonnes": "100.00",
        }]

        service = PriceSyncService()
        results = service.sync_records(test_data, "Alert Test Feed")

        assert results["created"] == 1
        assert len(results["alerts_triggered"]) == 1
        triggered = results["alerts_triggered"][0]
        assert triggered["user_id"] == user.id
        assert triggered["modal_price"] == 2780.0
        assert triggered["condition"] == "Above"


def test_price_tracker_search_and_filters_view(client, app):
    """Verify /prices/ view supports commodity and market search filters."""
    with app.app_context():
        service = PriceSyncService()
        service.sync(source="demo")

    # Search for Wheat in Gujarat
    response = client.get("/prices/?crop=Wheat&state=Gujarat")
    assert response.status_code == 200
    assert b"Agricultural Crop Price Tracker" in response.data
    assert b"Wheat" in response.data


def test_price_market_comparison_view(client, app):
    """Verify /prices/compare view displays inter-mandi price spread."""
    with app.app_context():
        service = PriceSyncService()
        service.sync(source="demo")

    response = client.get("/prices/compare?crop=Wheat+(Lokwan)")
    assert response.status_code == 200
    assert b"Inter-Mandi Crop Price Comparison" in response.data
    assert b"Mandi Rate Spread for" in response.data


def test_price_trends_chart_view(client, app):
    """Verify /prices/trends view returns historical time-series chart data."""
    with app.app_context():
        service = PriceSyncService()
        service.sync(source="demo")

    response = client.get("/prices/trends?crop=Wheat+(Lokwan)")
    assert response.status_code == 200
    assert b"Historical Crop Price Trends" in response.data
    assert b"historicalPriceChart" in response.data


def test_price_alert_create_and_delete_lifecycle(consumer_client, consumer_user, app):
    """Verify authenticated user can create and delete mandi price alerts."""
    with app.app_context():
        crop = Crop.query.first()
        market = Market.query.first()

    # 1. Create alert
    post_res = consumer_client.post(
        "/prices/alerts",
        data={
            "crop": crop.name,
            "market": market.name,
            "condition": "Above",
            "target_price": "3200",
        },
        follow_redirects=True,
    )
    assert post_res.status_code == 200
    assert b"configured successfully" in post_res.data

    with app.app_context():
        alert = PriceAlert.query.filter_by(user_id=consumer_user.id).first()
        assert alert is not None
        assert alert.target_price == Decimal("3200.00")
        alert_id = alert.id

    # 2. Delete alert
    del_res = consumer_client.post(
        f"/prices/alerts/delete/{alert_id}",
        follow_redirects=True,
    )
    assert del_res.status_code == 200
    assert b"removed successfully" in del_res.data

    with app.app_context():
        deleted = db.session.get(PriceAlert, alert_id)
        assert deleted is None
