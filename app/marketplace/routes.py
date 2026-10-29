from flask import render_template, request, flash, redirect, url_for
from app.marketplace import marketplace_bp
from app.auth.decorators import farmer_required

# Mock catalogue items used across marketplace views
DEMO_PRODUCTS = [
    {
        "id": 1,
        "name": "Fresh Organic Sharbati Wheat",
        "category": "Grains",
        "description": "Premium whole-wheat grain cultivated naturally in the fertile black soil of Saurashtra without chemical fertilizers. Ideal for soft, nutritious chapatis.",
        "price": 42.00,
        "unit": "kg",
        "stock": 450,
        "min_order": 5,
        "farmer_name": "Ramesh Patel",
        "farmer_phone": "+91 98765 43210",
        "location": "Rajkot, Gujarat",
        "is_active": True,
        "harvest_date": "March 2026",
        "image": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=800&q=80",
        "rating": 4.8,
        "reviews_count": 28,
    },
    {
        "id": 2,
        "name": "Desi Alphonso / Kesar Mangoes",
        "category": "Fruits",
        "description": "Naturally tree-ripened sweet organic mangoes harvested directly from Junagadh foothills. Handpicked and packed in hay boxes.",
        "price": 180.00,
        "unit": "kg",
        "stock": 80,
        "min_order": 2,
        "farmer_name": "Suresh Verma",
        "farmer_phone": "+91 98220 11223",
        "location": "Junagadh, Gujarat",
        "is_active": True,
        "harvest_date": "April 2026",
        "image": "https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=800&q=80",
        "rating": 4.9,
        "reviews_count": 42,
    },
    {
        "id": 3,
        "name": "Organic Red Onions",
        "category": "Vegetables",
        "description": "Firm, pungent medium-sized red onions with high dry-matter content for extended storage life. Farm graded.",
        "price": 30.00,
        "unit": "kg",
        "stock": 300,
        "min_order": 5,
        "farmer_name": "Bharat Bhai",
        "farmer_phone": "+91 94280 44556",
        "location": "Bhavnagar, Gujarat",
        "is_active": True,
        "harvest_date": "February 2026",
        "image": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
        "rating": 4.7,
        "reviews_count": 19,
    },
    {
        "id": 4,
        "name": "Cold-Pressed Groundnut Oil",
        "category": "Oils & Seeds",
        "description": "Unrefined, traditionally pressed Saurashtra groundnut oil rich in antioxidants and natural aroma.",
        "price": 210.00,
        "unit": "litre",
        "stock": 65,
        "min_order": 1,
        "farmer_name": "Kishore Solanki",
        "farmer_phone": "+91 97230 77889",
        "location": "Gondal, Gujarat",
        "is_active": True,
        "harvest_date": "January 2026",
        "image": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=800&q=80",
        "rating": 5.0,
        "reviews_count": 35,
    },
    {
        "id": 5,
        "name": "Fresh Organic Potatoes",
        "category": "Vegetables",
        "description": "Directly dug soil-cured medium tubers suitable for daily cooking and curries. Chemical residue free.",
        "price": 25.00,
        "unit": "kg",
        "stock": 500,
        "min_order": 5,
        "farmer_name": "Ramesh Patel",
        "farmer_phone": "+91 98765 43210",
        "location": "Rajkot, Gujarat",
        "is_active": True,
        "harvest_date": "March 2026",
        "image": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=800&q=80",
        "rating": 4.6,
        "reviews_count": 14,
    },
    {
        "id": 6,
        "name": "Unjha High-Grade Cumin (Jeera)",
        "category": "Spices",
        "description": "Premium sortex cleaned cumin seeds with exceptional essential oil content, sourced from the hub of Asian spice trade.",
        "price": 340.00,
        "unit": "kg",
        "stock": 0,  # Demonstrating out-of-stock badge
        "min_order": 1,
        "farmer_name": "Nitin Prajapati",
        "farmer_phone": "+91 98980 99001",
        "location": "Unjha, Gujarat",
        "is_active": False,
        "harvest_date": "March 2026",
        "image": "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=800&q=80",
        "rating": 4.9,
        "reviews_count": 51,
    },
]


@marketplace_bp.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    category = request.args.get("category", "")
    sort_by = request.args.get("sort", "featured")

    filtered = DEMO_PRODUCTS
    if q:
        filtered = [p for p in filtered if q in p["name"].lower() or q in p["description"].lower() or q in p["location"].lower()]
    if category:
        filtered = [p for p in filtered if p["category"].lower() == category.lower()]

    if sort_by == "price_low":
        filtered = sorted(filtered, key=lambda x: x["price"])
    elif sort_by == "price_high":
        filtered = sorted(filtered, key=lambda x: x["price"], reverse=True)
    elif sort_by == "rating":
        filtered = sorted(filtered, key=lambda x: x["rating"], reverse=True)

    categories = ["Grains", "Vegetables", "Fruits", "Oils & Seeds", "Spices", "Pulses"]
    return render_template("marketplace/index.html", products=filtered, categories=categories, current_category=category, query=q, sort_by=sort_by)


@marketplace_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = next((p for p in DEMO_PRODUCTS if p["id"] == product_id), DEMO_PRODUCTS[0])
    related = [p for p in DEMO_PRODUCTS if p["id"] != product["id"] and p["category"] == product["category"]][:3]
    return render_template("marketplace/detail.html", product=product, related_products=related)


@marketplace_bp.route("/farmer/dashboard")
@farmer_required
def farmer_dashboard():
    # Metrics for farmer dashboard
    stats = {
        "total_revenue": 68450.00,
        "active_listings": 4,
        "total_orders": 38,
        "pending_shipments": 5,
    }
    recent_orders = [
        {"order_id": "#ORD-8921", "customer": "Anand Shah", "date": "Today, 10:30 AM", "amount": 1260.00, "status": "Pending", "items": "30 kg Wheat"},
        {"order_id": "#ORD-8919", "customer": "Pooja Mehta", "date": "Yesterday", "amount": 630.00, "status": "Confirmed", "items": "3 Litres Groundnut Oil"},
        {"order_id": "#ORD-8904", "customer": "Vikram Desai", "date": "27 Oct 2026", "amount": 450.00, "status": "Delivered", "items": "15 kg Onions"},
    ]
    return render_template("marketplace/farmer_dashboard.html", stats=stats, recent_orders=recent_orders)


@marketplace_bp.route("/farmer/listings")
@farmer_required
def manage_listings():
    # Only showing listings belonging to Ramesh Patel (farmer view)
    farmer_listings = [p for p in DEMO_PRODUCTS if p["farmer_name"] == "Ramesh Patel"]
    return render_template("marketplace/manage_listings.html", listings=farmer_listings)


@marketplace_bp.route("/farmer/listings/new", methods=["GET", "POST"])
@farmer_required
def new_listing():
    if request.method == "POST":
        flash("Produce listing published successfully to the marketplace!", "success")
        return redirect(url_for("marketplace.manage_listings"))
    return render_template("marketplace/listing_form.html", action="Create")


@marketplace_bp.route("/farmer/listings/<int:listing_id>/edit", methods=["GET", "POST"])
@farmer_required
def edit_listing(listing_id):
    listing = next((p for p in DEMO_PRODUCTS if p["id"] == listing_id), DEMO_PRODUCTS[0])
    if request.method == "POST":
        flash("Listing updated successfully.", "success")
        return redirect(url_for("marketplace.manage_listings"))
    return render_template("marketplace/listing_form.html", action="Edit", listing=listing)
