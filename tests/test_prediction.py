from decimal import Decimal
import pytest
from app.services.price_predictor import PricePredictorService
from app.models.price import Crop, Market, CropPriceRecord


def test_price_predictor_forecast_math(app):
    """Verify time-series regression slope, volatility bounds, and forecast trajectory."""
    with app.app_context():
        predictor = PricePredictorService()
        result = predictor.forecast_crop_price(crop_name="Wheat (Lokwan)", state="All India", days_ahead=7)

        assert result is not None
        assert result["current_price"] > 0
        assert result["predicted_price_7d"] > 0
        assert len(result["forecast_labels"]) == 7
        assert len(result["forecast_predicted"]) == 7
        assert len(result["forecast_upper"]) == 7
        assert len(result["forecast_lower"]) == 7

        # Verify mathematical confidence envelope bounds
        for pred, upper, lower in zip(result["forecast_predicted"], result["forecast_upper"], result["forecast_lower"]):
            assert upper >= pred >= lower
            assert lower > 0

        assert result["trend"] in {"Bullish", "Bearish", "Stable"}
        assert len(result["recommendation"]) > 10


def test_price_predictor_state_predictions_pan_india(app):
    """Verify pan-India comparative state predictions return sorted market opportunities."""
    with app.app_context():
        predictor = PricePredictorService()
        state_list = predictor.get_all_india_state_predictions(crop_name="Wheat (Lokwan)")

        assert len(state_list) > 0
        for entry in state_list:
            assert "state" in entry
            assert entry["current_modal"] > 0
            assert entry["predicted_modal_7d"] > 0
            assert entry["trend"] in {"Bullish", "Bearish", "Stable"}

        # Verify list is ordered from highest predicted price down (best selling opportunities)
        for i in range(len(state_list) - 1):
            assert state_list[i]["predicted_modal_7d"] >= state_list[i + 1]["predicted_modal_7d"]


def test_price_prediction_view_loads_successfully(client, app):
    """Verify /prices/predict view renders Chart.js forecast and national market table."""
    response = client.get("/prices/predict?crop=Wheat+(Lokwan)&state=All+India")
    assert response.status_code == 200
    assert b"Pan-India Market Price Prediction" in response.data
    assert b"predictionChart" in response.data
    assert b"Pan-India State-by-State Price Forecasts" in response.data


def test_price_prediction_view_with_unknown_crop_handles_gracefully(client, app):
    """Verify that predicting a commodity with no database records falls back gracefully without crashing."""
    response = client.get("/prices/predict?crop=ExoticCropNotFound123")
    assert response.status_code == 200
    assert b"Pan-India Market Price Prediction" in response.data
    assert b"predictionChart" in response.data
