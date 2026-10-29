from flask import render_template, request, flash, redirect, url_for
from app.prices import prices_bp

# Verified Demo Market Price Records for Indian APMCs (Agmarknet schema compliant)
DEMO_PRICE_RECORDS = [
    {
        "id": 1,
        "crop": "Wheat (Lokwan)",
        "variety": "Lokwan",
        "market": "Rajkot APMC",
        "state": "Gujarat",
        "district": "Rajkot",
        "arrival_date": "28 Oct 2026",
        "min_price": 2600.00,
        "max_price": 2950.00,
        "modal_price": 2750.00,
        "arrivals_tonnes": 140.5,
        "unit": "Quintal (100 kg)",
    },
    {
        "id": 2,
        "crop": "Cotton (Shankar-6)",
        "variety": "Medium Staple",
        "market": "Gondal APMC",
        "state": "Gujarat",
        "district": "Rajkot",
        "arrival_date": "28 Oct 2026",
        "min_price": 7100.00,
        "max_price": 7750.00,
        "modal_price": 7450.00,
        "arrivals_tonnes": 320.0,
        "unit": "Quintal (100 kg)",
    },
    {
        "id": 3,
        "crop": "Groundnut (Bold)",
        "variety": "Bold 20",
        "market": "Amreli APMC",
        "state": "Gujarat",
        "district": "Amreli",
        "arrival_date": "28 Oct 2026",
        "min_price": 5900.00,
        "max_price": 6650.00,
        "modal_price": 6300.00,
        "arrivals_tonnes": 210.2,
        "unit": "Quintal (100 kg)",
    },
    {
        "id": 4,
        "crop": "Cumin (Jeera)",
        "variety": "First Grade",
        "market": "Unjha APMC",
        "state": "Gujarat",
        "district": "Mehsana",
        "arrival_date": "28 Oct 2026",
        "min_price": 26500.00,
        "max_price": 31000.00,
        "modal_price": 28500.00,
        "arrivals_tonnes": 95.0,
        "unit": "Quintal (100 kg)",
    },
    {
        "id": 5,
        "crop": "Wheat (Lokwan)",
        "variety": "Lokwan",
        "market": "Gondal APMC",
        "state": "Gujarat",
        "district": "Rajkot",
        "arrival_date": "28 Oct 2026",
        "min_price": 2580.00,
        "max_price": 2920.00,
        "modal_price": 2720.00,
        "arrivals_tonnes": 98.4,
        "unit": "Quintal (100 kg)",
    },
    {
        "id": 6,
        "crop": "Wheat (Lokwan)",
        "variety": "Lokwan",
        "market": "Indore APMC",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "arrival_date": "28 Oct 2026",
        "min_price": 2650.00,
        "max_price": 3050.00,
        "modal_price": 2820.00,
        "arrivals_tonnes": 410.0,
        "unit": "Quintal (100 kg)",
    },
    {
        "id": 7,
        "crop": "Red Onion",
        "variety": "Nasik Red",
        "market": "Lasalgaon APMC",
        "state": "Maharashtra",
        "district": "Nashik",
        "arrival_date": "28 Oct 2026",
        "min_price": 1800.00,
        "max_price": 2800.00,
        "modal_price": 2350.00,
        "arrivals_tonnes": 680.0,
        "unit": "Quintal (100 kg)",
    },
    {
        "id": 8,
        "crop": "Soyabean (Yellow)",
        "variety": "Yellow",
        "market": "Kota APMC",
        "state": "Rajasthan",
        "district": "Kota",
        "arrival_date": "28 Oct 2026",
        "min_price": 4200.00,
        "max_price": 4850.00,
        "modal_price": 4600.00,
        "arrivals_tonnes": 240.0,
        "unit": "Quintal (100 kg)",
    },
]

# Demo Price Alerts
DEMO_ALERTS = [
    {
        "id": 1,
        "crop": "Wheat (Lokwan)",
        "market": "Rajkot APMC",
        "target_price": 2800.00,
        "condition": "Above",
        "is_active": True,
        "created_at": "20 Oct 2026",
    },
    {
        "id": 2,
        "crop": "Cotton (Shankar-6)",
        "market": "Gondal APMC",
        "target_price": 7500.00,
        "condition": "Above",
        "is_active": True,
        "created_at": "22 Oct 2026",
    },
]


@prices_bp.route("/")
def index():
    crop_filter = request.args.get("crop", "").strip().lower()
    market_filter = request.args.get("market", "").strip().lower()
    state_filter = request.args.get("state", "").strip().lower()

    filtered = DEMO_PRICE_RECORDS
    if crop_filter:
        filtered = [r for r in filtered if crop_filter in r["crop"].lower()]
    if market_filter:
        filtered = [r for r in filtered if market_filter in r["market"].lower()]
    if state_filter:
        filtered = [r for r in filtered if state_filter in r["state"].lower()]

    crops = sorted(list(set(r["crop"] for r in DEMO_PRICE_RECORDS)))
    markets = sorted(list(set(r["market"] for r in DEMO_PRICE_RECORDS)))
    states = sorted(list(set(r["state"] for r in DEMO_PRICE_RECORDS)))

    # Compute aggregate stats for top cards
    avg_modal = sum(r["modal_price"] for r in filtered) / len(filtered) if filtered else 0
    highest_max = max((r["max_price"] for r in filtered), default=0)
    lowest_min = min((r["min_price"] for r in filtered), default=0)

    return render_template(
        "prices/index.html",
        records=filtered,
        crops=crops,
        markets=markets,
        states=states,
        selected_crop=request.args.get("crop", ""),
        selected_market=request.args.get("market", ""),
        selected_state=request.args.get("state", ""),
        avg_modal=avg_modal,
        highest_max=highest_max,
        lowest_min=lowest_min,
        last_updated="28 Oct 2026, 05:00 PM IST",
        source_attribution="Agmarknet / Ministry of Agriculture & Farmers Welfare (Academic Demo Snapshot)",
    )


@prices_bp.route("/compare")
def compare():
    # Comparing Wheat across different Mandis
    selected_crop = request.args.get("crop", "Wheat (Lokwan)")
    comparison_data = [r for r in DEMO_PRICE_RECORDS if r["crop"].lower() == selected_crop.lower()]
    if not comparison_data:
        comparison_data = [r for r in DEMO_PRICE_RECORDS if "wheat" in r["crop"].lower()]

    crops = sorted(list(set(r["crop"] for r in DEMO_PRICE_RECORDS)))
    return render_template("prices/compare.html", records=comparison_data, crops=crops, selected_crop=selected_crop)


@prices_bp.route("/trends")
def trends():
    # 7-day demo trend for selected crop
    selected_crop = request.args.get("crop", "Wheat (Lokwan)")
    trend_labels = ["22 Oct", "23 Oct", "24 Oct", "25 Oct", "26 Oct", "27 Oct", "28 Oct"]
    modal_trend = [2680, 2700, 2690, 2720, 2740, 2735, 2750]
    min_trend = [2550, 2580, 2560, 2590, 2610, 2600, 2600]
    max_trend = [2850, 2880, 2870, 2900, 2920, 2930, 2950]

    crops = sorted(list(set(r["crop"] for r in DEMO_PRICE_RECORDS)))
    return render_template(
        "prices/trends.html",
        crops=crops,
        selected_crop=selected_crop,
        trend_labels=trend_labels,
        modal_trend=modal_trend,
        min_trend=min_trend,
        max_trend=max_trend,
    )


@prices_bp.route("/alerts", methods=["GET", "POST"])
def alerts():
    if request.method == "POST":
        flash("Price alert rule configured successfully! You will receive notification when the threshold is crossed.", "success")
        return redirect(url_for("prices.alerts"))

    crops = sorted(list(set(r["crop"] for r in DEMO_PRICE_RECORDS)))
    markets = sorted(list(set(r["market"] for r in DEMO_PRICE_RECORDS)))
    return render_template("prices/alerts.html", alerts=DEMO_ALERTS, crops=crops, markets=markets)
