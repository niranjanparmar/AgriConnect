from flask import render_template
from app.main import main_bp


@main_bp.route("/")
def index():
    # Featured produce items for the home page showcase
    featured_products = [
        {
            "id": 1,
            "name": "Fresh Organic Sharbati Wheat",
            "category": "Grains",
            "price": 42.00,
            "unit": "kg",
            "stock": 450,
            "farmer_name": "Ramesh Patel",
            "location": "Rajkot, Gujarat",
            "image": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=600&q=80",
            "rating": 4.8,
        },
        {
            "id": 2,
            "name": "Desi Alphonso Mangoes",
            "category": "Fruits",
            "price": 180.00,
            "unit": "kg",
            "stock": 80,
            "farmer_name": "Suresh Verma",
            "location": "Junagadh, Gujarat",
            "image": "https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=600&q=80",
            "rating": 4.9,
        },
        {
            "id": 3,
            "name": "Organic Red Onions",
            "category": "Vegetables",
            "price": 30.00,
            "unit": "kg",
            "stock": 300,
            "farmer_name": "Bharat Bhai",
            "location": "Nashik / Bhavnagar",
            "image": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80",
            "rating": 4.7,
        },
        {
            "id": 4,
            "name": "Pure Desi Groundnut Oil",
            "category": "Oils & Seeds",
            "price": 210.00,
            "unit": "litre",
            "stock": 65,
            "farmer_name": "Kishore Solanki",
            "location": "Gondal, Gujarat",
            "image": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=600&q=80",
            "rating": 5.0,
        },
    ]

    # Live Mandi Rate Highlights for the ticker
    price_highlights = [
        {"crop": "Wheat (Lokwan)", "market": "Rajkot APMC", "modal_price": 2750, "unit": "Quintal", "change": "+1.8%"},
        {"crop": "Cotton (Shankar-6)", "market": "Gondal APMC", "modal_price": 7450, "unit": "Quintal", "change": "-0.5%"},
        {"crop": "Groundnut", "market": "Amreli APMC", "modal_price": 6300, "unit": "Quintal", "change": "+2.4%"},
        {"crop": "Cumin (Jeera)", "market": "Unjha APMC", "modal_price": 28500, "unit": "Quintal", "change": "+3.1%"},
    ]

    return render_template("main/index.html", products=featured_products, price_highlights=price_highlights)


@main_bp.route("/about")
def about():
    return render_template("main/about.html")


@main_bp.route("/contact")
def contact():
    return render_template("main/contact.html")
