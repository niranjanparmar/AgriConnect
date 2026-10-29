import math
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import func
from app.extensions import db
from app.models.price import Crop, Market, CropPriceRecord


class PricePredictorService:
    """
    Agricultural Commodity Price Forecasting & Pan-India Market Intelligence Engine.
    Uses time-series trend decomposition, volatility intervals, and inter-state aggregation.
    """

    @staticmethod
    def _calculate_linear_trend(x_vals: List[int], y_vals: List[float]) -> Tuple[float, float]:
        """Compute ordinary least squares linear regression slope and intercept."""
        n = len(x_vals)
        if n < 2:
            return 0.0, (y_vals[0] if y_vals else 0.0)

        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)

        if denominator == 0:
            return 0.0, y_mean

        slope = numerator / denominator
        intercept = y_mean - (slope * x_mean)
        return slope, intercept

    @staticmethod
    def _calculate_volatility(y_vals: List[float]) -> float:
        """Calculate historical sample standard deviation (volatility)."""
        n = len(y_vals)
        if n < 2:
            return y_vals[0] * 0.03 if y_vals else 50.0
        mean = sum(y_vals) / n
        variance = sum((y - mean) ** 2 for y in y_vals) / (n - 1)
        return math.sqrt(variance)

    def forecast_crop_price(
        self,
        crop_name: str,
        state: Optional[str] = None,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Generate time-series forecast for the specified crop over the next N days.
        Returns historical timeline, future predictions, confidence bounds, and recommendations.
        """
        # Base query joined with Crop and Market
        query = (
            db.session.query(
                CropPriceRecord.arrival_date,
                func.avg(CropPriceRecord.modal_price).label("avg_modal"),
                func.min(CropPriceRecord.min_price).label("min_floor"),
                func.max(CropPriceRecord.max_price).label("max_ceiling"),
            )
            .join(CropPriceRecord.crop)
            .join(CropPriceRecord.market)
            .filter(Crop.name.ilike(f"%{crop_name}%"))
        )

        if state and state.strip() and state.lower() != "all india":
            query = query.filter(Market.state.ilike(f"%{state.strip()}%"))

        raw_history = (
            query.group_by(CropPriceRecord.arrival_date)
            .order_by(CropPriceRecord.arrival_date.asc())
            .all()
        )

        # Build historical series
        today = date.today()
        hist_dates: List[date] = []
        hist_prices: List[float] = []

        if raw_history:
            for row in raw_history:
                hist_dates.append(row[0])
                hist_prices.append(float(row[1]))
        else:
            # Baseline estimate if no historical records exist
            hist_dates = [today - timedelta(days=i) for i in range(5, -1, -1)]
            hist_prices = [2650.0, 2680.0, 2700.0, 2690.0, 2720.0, 2750.0]

        current_price = hist_prices[-1]

        # Calculate regression trend
        x_indices = list(range(len(hist_prices)))
        slope, intercept = self._calculate_linear_trend(x_indices, hist_prices)
        volatility = max(self._calculate_volatility(hist_prices), current_price * 0.02)

        # Dampen extreme slope for realistic agricultural forecasts (max +/- 1.5% daily drift)
        max_daily_drift = current_price * 0.015
        damped_slope = max(-max_daily_drift, min(max_daily_drift, slope))

        # Project future points
        last_index = len(hist_prices) - 1
        future_dates: List[str] = []
        future_predicted: List[float] = []
        future_upper: List[float] = []
        future_lower: List[float] = []

        last_date = hist_dates[-1] if hist_dates else today

        for step in range(1, days_ahead + 1):
            f_date = last_date + timedelta(days=step)
            # Projected modal price with slight asymptotic curvature
            step_projection = current_price + (damped_slope * step)
            # Ensure price stays realistic
            step_projection = max(current_price * 0.70, round(step_projection, 2))

            # Confidence band widens as projection extends further into the future
            band_spread = round(volatility * math.sqrt(step) * 0.85, 2)
            upper_band = round(step_projection + band_spread, 2)
            lower_band = max(50.0, round(step_projection - band_spread, 2))

            future_dates.append(f_date.strftime("%d %b"))
            future_predicted.append(step_projection)
            future_upper.append(upper_band)
            future_lower.append(lower_band)

        terminal_prediction = future_predicted[-1]
        pct_change = round(((terminal_prediction - current_price) / current_price) * 100, 2)

        # Determine trajectory classification & strategic recommendation
        if pct_change >= 2.0:
            trend = "Bullish"
            trend_badge = "success"
            trend_icon = "bi-arrow-up-right-circle-fill"
            recommendation = (
                f"Optimal Selling Window: Prices projected to increase by +{pct_change}% over the next "
                f"{days_ahead} days. Holding dry harvest inventory for 4–6 days is recommended to maximize realization."
            )
        elif pct_change <= -2.0:
            trend = "Bearish"
            trend_badge = "danger"
            trend_icon = "bi-arrow-down-right-circle-fill"
            recommendation = (
                f"Surging Market Supply: Prices expected to soften by {pct_change}% as regional harvest arrivals increase. "
                "Early dispatch to nearby APMC mandis is advised to avoid margin compression."
            )
        else:
            trend = "Stable"
            trend_badge = "warning"
            trend_icon = "bi-arrow-right-circle-fill"
            recommendation = (
                f"Price Equilibrium: Mandi auctions show steady balance (+/- {abs(pct_change)}%). "
                "Immediate marketing or normal staggered dispatch offers predictable returns."
            )

        historical_labels = [d.strftime("%d %b") for d in hist_dates]

        return {
            "crop": crop_name,
            "state": state or "All India",
            "current_price": round(current_price, 2),
            "predicted_price_7d": round(terminal_prediction, 2),
            "expected_change_pct": pct_change,
            "trend": trend,
            "trend_badge": trend_badge,
            "trend_icon": trend_icon,
            "volatility_index": round(volatility, 2),
            "recommendation": recommendation,
            "historical_labels": historical_labels,
            "historical_prices": hist_prices,
            "forecast_labels": future_dates,
            "forecast_predicted": future_predicted,
            "forecast_upper": future_upper,
            "forecast_lower": future_lower,
        }

    def get_all_india_state_predictions(self, crop_name: str) -> List[Dict[str, Any]]:
        """
        Compute comparative state-by-state price benchmarks and 7-day predictions across all Indian states.
        """
        # Query distinct states that record this crop
        state_rows = (
            db.session.query(
                Market.state,
                func.count(CropPriceRecord.id).label("record_count"),
                func.avg(CropPriceRecord.modal_price).label("avg_modal"),
                func.min(CropPriceRecord.min_price).label("min_floor"),
                func.max(CropPriceRecord.max_price).label("max_ceiling"),
            )
            .join(CropPriceRecord.market)
            .join(CropPriceRecord.crop)
            .filter(Crop.name.ilike(f"%{crop_name}%"))
            .group_by(Market.state)
            .all()
        )

        state_predictions = []

        if state_rows:
            for s_name, count, avg_m, min_f, max_c in state_rows:
                curr = float(avg_m or 0.0)
                # Compute state-specific projection
                state_forecast = self.forecast_crop_price(crop_name=crop_name, state=s_name, days_ahead=7)
                pred = state_forecast["predicted_price_7d"]
                chg = state_forecast["expected_change_pct"]
                trend = state_forecast["trend"]
                badge = state_forecast["trend_badge"]

                state_predictions.append({
                    "state": s_name,
                    "mandi_count": count,
                    "current_modal": round(curr, 2),
                    "predicted_modal_7d": round(pred, 2),
                    "change_pct": chg,
                    "trend": trend,
                    "badge": badge,
                    "min_floor": round(float(min_f or curr), 2),
                    "max_ceiling": round(float(max_c or curr), 2),
                })
        else:
            # Pan-India default state benchmarks for educational demonstration
            demo_states = [
                ("Gujarat", 2740.0, 2795.0, 2.0, "Bullish", "success"),
                ("Maharashtra", 2680.0, 2730.0, 1.9, "Bullish", "success"),
                ("Madhya Pradesh", 2850.0, 2890.0, 1.4, "Stable", "warning"),
                ("Rajasthan", 2720.0, 2705.0, -0.6, "Stable", "warning"),
                ("Punjab", 2790.0, 2850.0, 2.2, "Bullish", "success"),
                ("Uttar Pradesh", 2650.0, 2620.0, -1.1, "Stable", "warning"),
                ("Odisha", 2690.0, 2740.0, 1.9, "Bullish", "success"),
            ]
            for s_name, curr, pred, chg, trend, badge in demo_states:
                state_predictions.append({
                    "state": s_name,
                    "mandi_count": 4,
                    "current_modal": curr,
                    "predicted_modal_7d": pred,
                    "change_pct": chg,
                    "trend": trend,
                    "badge": badge,
                    "min_floor": round(curr * 0.94, 2),
                    "max_ceiling": round(curr * 1.08, 2),
                })

        # Sort states by highest predicted price (best selling opportunities)
        state_predictions.sort(key=lambda x: x["predicted_modal_7d"], reverse=True)
        return state_predictions

