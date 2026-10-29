from decimal import Decimal
from datetime import date, datetime, timezone
import click
from flask import Blueprint
from app.extensions import db
from app.models.user import User, FarmerProfile
from app.models.marketplace import Category, ProduceListing, CartItem
from app.models.order import Order, DeliveryDetail, OrderItem
from app.models.price import Crop, Market, CropPriceRecord, PriceAlert

cli_bp = Blueprint("cli", __name__)


@cli_bp.cli.command("seed")
def seed():
    """Seed database with realistic initial categories, demo users, produce listings, and APMC rates."""
    click.echo("Seeding AgriConnect database...")

    # 1. Categories
    categories_data = [
        {"name": "Grains & Cereals", "slug": "grains", "description": "Wheat, rice, millet, and staple cereal grains."},
        {"name": "Fresh Vegetables", "slug": "vegetables", "description": "Farm-fresh daily seasonal vegetables."},
        {"name": "Fresh Fruits", "slug": "fruits", "description": "Tree-ripened orchard fruits and mangoes."},
        {"name": "Oils & Seeds", "slug": "oils-seeds", "description": "Cold-pressed edible oils and oilseeds."},
        {"name": "Spices & Herbs", "slug": "spices", "description": "Regional spice seeds, cumin, coriander, and turmeric."},
        {"name": "Pulses & Dal", "slug": "pulses", "description": "High-protein unpolished pulses and lentils."},
    ]

    cat_map = {}
    for c_data in categories_data:
        cat = Category.query.filter_by(slug=c_data["slug"]).first()
        if not cat:
            cat = Category(**c_data)
            db.session.add(cat)
            db.session.flush()
        cat_map[c_data["slug"]] = cat
    click.echo(f"  [OK] Processed {len(categories_data)} categories")

    # 2. Demo Users
    # Farmer User
    farmer_user = User.query.filter_by(email="farmer@agriconnect.local").first()
    if not farmer_user:
        farmer_user = User(
            email="farmer@agriconnect.local",
            full_name="Ramesh Patel",
            phone="+91 98765 43210",
            role="farmer",
            is_active_account=True,
        )
        farmer_user.set_password("FarmerPass123!")
        db.session.add(farmer_user)
        db.session.flush()

        farmer_profile = FarmerProfile(
            user_id=farmer_user.id,
            farm_name="Patel Organic Orchards",
            farm_address="Survey No 42, Gondal Road, Near Market Yard",
            district="Rajkot",
            state="Gujarat",
            pincode="360004",
            is_verified=True,
            bio="Third-generation organic farmer specializing in Sharbati wheat, local onions, and cold-pressed oilseeds.",
        )
        db.session.add(farmer_profile)
        db.session.flush()
    else:
        farmer_profile = farmer_user.farmer_profile
    click.echo("  [OK] Processed demo Farmer user (farmer@agriconnect.local / FarmerPass123!)")

    # Consumer User
    consumer_user = User.query.filter_by(email="consumer@agriconnect.local").first()
    if not consumer_user:
        consumer_user = User(
            email="consumer@agriconnect.local",
            full_name="Anand Shah",
            phone="+91 98250 12345",
            role="consumer",
            is_active_account=True,
        )
        consumer_user.set_password("ConsumerPass123!")
        db.session.add(consumer_user)
        db.session.flush()
    click.echo("  [OK] Processed demo Consumer user (consumer@agriconnect.local / ConsumerPass123!)")

    # 3. Produce Listings
    listings_data = [
        {
            "name": "Fresh Organic Sharbati Wheat",
            "category_slug": "grains",
            "price": Decimal("42.00"),
            "unit": "kg",
            "stock": Decimal("450.00"),
            "min_order": Decimal("5.00"),
            "location": "Rajkot, Gujarat",
            "image": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=800&q=80",
            "desc": "Premium whole-wheat grain cultivated naturally in Saurashtra black soil without synthetic chemical fertilizers.",
        },
        {
            "name": "Desi Alphonso / Kesar Mangoes",
            "category_slug": "fruits",
            "price": Decimal("180.00"),
            "unit": "kg",
            "stock": Decimal("80.00"),
            "min_order": Decimal("2.00"),
            "location": "Junagadh, Gujarat",
            "image": "https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=800&q=80",
            "desc": "Naturally tree-ripened sweet organic mangoes harvested directly from Junagadh foothills.",
        },
        {
            "name": "Organic Red Onions",
            "category_slug": "vegetables",
            "price": Decimal("30.00"),
            "unit": "kg",
            "stock": Decimal("300.00"),
            "min_order": Decimal("5.00"),
            "location": "Bhavnagar, Gujarat",
            "image": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=80",
            "desc": "Firm, pungent medium-sized red onions with high dry-matter content for extended storage life.",
        },
        {
            "name": "Cold-Pressed Groundnut Oil",
            "category_slug": "oils-seeds",
            "price": Decimal("210.00"),
            "unit": "litre",
            "stock": Decimal("65.00"),
            "min_order": Decimal("1.00"),
            "location": "Gondal, Gujarat",
            "image": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=800&q=80",
            "desc": "Unrefined, traditionally pressed Saurashtra groundnut oil rich in natural aroma and antioxidants.",
        },
    ]

    for l_data in listings_data:
        existing = ProduceListing.query.filter_by(name=l_data["name"], farmer_id=farmer_profile.id).first()
        if not existing:
            listing = ProduceListing(
                farmer_id=farmer_profile.id,
                category_id=cat_map[l_data["category_slug"]].id,
                name=l_data["name"],
                description=l_data["desc"],
                price_per_unit=l_data["price"],
                unit=l_data["unit"],
                stock_quantity=l_data["stock"],
                min_order_quantity=l_data["min_order"],
                location=l_data["location"],
                image_url=l_data["image"],
                is_active=True,
            )
            db.session.add(listing)
    click.echo(f"  [OK] Processed {len(listings_data)} produce listings")

    # 4. Crops and Mandis for Price Tracker
    crops_info = [
        {"name": "Wheat (Lokwan)", "category": "Cereal", "unit": "Quintal (100 kg)"},
        {"name": "Cotton (Shankar-6)", "category": "Fiber", "unit": "Quintal (100 kg)"},
        {"name": "Groundnut (Bold)", "category": "Oilseed", "unit": "Quintal (100 kg)"},
        {"name": "Cumin (Jeera)", "category": "Spices", "unit": "Quintal (100 kg)"},
        {"name": "Red Onion", "category": "Vegetable", "unit": "Quintal (100 kg)"},
        {"name": "Soyabean (Yellow)", "category": "Oilseed", "unit": "Quintal (100 kg)"},
    ]

    crop_entities = {}
    for ci in crops_info:
        cr = Crop.query.filter_by(name=ci["name"]).first()
        if not cr:
            cr = Crop(name=ci["name"], category=ci["category"], standard_unit=ci["unit"])
            db.session.add(cr)
            db.session.flush()
        crop_entities[ci["name"]] = cr

    markets_info = [
        {"name": "Rajkot APMC", "district": "Rajkot", "state": "Gujarat", "apmc_code": "GJ-RJK-01"},
        {"name": "Gondal APMC", "district": "Rajkot", "state": "Gujarat", "apmc_code": "GJ-GDL-02"},
        {"name": "Amreli APMC", "district": "Amreli", "state": "Gujarat", "apmc_code": "GJ-AMR-03"},
        {"name": "Unjha APMC", "district": "Mehsana", "state": "Gujarat", "apmc_code": "GJ-UNJ-04"},
        {"name": "Lasalgaon APMC", "district": "Nashik", "state": "Maharashtra", "apmc_code": "MH-LSG-01"},
        {"name": "Indore APMC", "district": "Indore", "state": "Madhya Pradesh", "apmc_code": "MP-IND-01"},
        {"name": "Kota APMC", "district": "Kota", "state": "Rajasthan", "apmc_code": "RJ-KTA-01"},
    ]

    market_entities = {}
    for mi in markets_info:
        mk = Market.query.filter_by(name=mi["name"]).first()
        if not mk:
            mk = Market(name=mi["name"], district=mi["district"], state=mi["state"], apmc_code=mi["apmc_code"])
            db.session.add(mk)
            db.session.flush()
        market_entities[mi["name"]] = mk

    # 5. Daily Mandi Crop Price Records
    sample_prices = [
        ("Wheat (Lokwan)", "Rajkot APMC", "Lokwan", date(2026, 10, 28), Decimal("2600.00"), Decimal("2950.00"), Decimal("2750.00"), Decimal("140.5")),
        ("Wheat (Lokwan)", "Gondal APMC", "Lokwan", date(2026, 10, 28), Decimal("2580.00"), Decimal("2920.00"), Decimal("2720.00"), Decimal("98.4")),
        ("Wheat (Lokwan)", "Indore APMC", "Lokwan", date(2026, 10, 28), Decimal("2650.00"), Decimal("3050.00"), Decimal("2820.00"), Decimal("410.0")),
        ("Cotton (Shankar-6)", "Gondal APMC", "Medium Staple", date(2026, 10, 28), Decimal("7100.00"), Decimal("7750.00"), Decimal("7450.00"), Decimal("320.0")),
        ("Groundnut (Bold)", "Amreli APMC", "Bold 20", date(2026, 10, 28), Decimal("5900.00"), Decimal("6650.00"), Decimal("6300.00"), Decimal("210.2")),
        ("Cumin (Jeera)", "Unjha APMC", "First Grade", date(2026, 10, 28), Decimal("26500.00"), Decimal("31000.00"), Decimal("28500.00"), Decimal("95.0")),
        ("Red Onion", "Lasalgaon APMC", "Nasik Red", date(2026, 10, 28), Decimal("1800.00"), Decimal("2800.00"), Decimal("2350.00"), Decimal("680.0")),
        ("Soyabean (Yellow)", "Kota APMC", "Yellow", date(2026, 10, 28), Decimal("4200.00"), Decimal("4850.00"), Decimal("4600.00"), Decimal("240.0")),
    ]

    for crop_name, mkt_name, var, dt, p_min, p_max, p_mod, arr_ton in sample_prices:
        c_obj = crop_entities[crop_name]
        m_obj = market_entities[mkt_name]
        r_hash = CropPriceRecord.generate_hash(c_obj.id, m_obj.id, var, dt)
        
        existing_price = CropPriceRecord.query.filter_by(record_hash=r_hash).first()
        if not existing_price:
            price_rec = CropPriceRecord(
                crop_id=c_obj.id,
                market_id=m_obj.id,
                variety=var,
                arrival_date=dt,
                min_price=p_min,
                max_price=p_max,
                modal_price=p_mod,
                arrivals_tonnes=arr_ton,
                source="Agmarknet",
                record_hash=r_hash,
            )
            db.session.add(price_rec)
    click.echo(f"  [OK] Processed {len(sample_prices)} APMC Mandi price records (Idempotent / No Duplicates)")

    # 6. Sample Order and Delivery Detail
    existing_order = Order.query.filter_by(order_number="AGC-2026-8921").first()
    if not existing_order:
        wheat_listing = ProduceListing.query.filter_by(name="Fresh Organic Sharbati Wheat").first()
        order = Order(
            order_number="AGC-2026-8921",
            consumer_id=consumer_user.id,
            total_amount=Decimal("1100.00"),
            delivery_fee=Decimal("50.00"),
            status="Confirmed",
            payment_method="Cash on Delivery",
        )
        db.session.add(order)
        db.session.flush()

        del_detail = DeliveryDetail(
            order_id=order.id,
            recipient_name="Anand Shah",
            phone="+91 98250 12345",
            address_line="Flat 302, Green Park Residency, Kalawad Road",
            city="Rajkot",
            state="Gujarat",
            pincode="360005",
            delivery_instructions="Please call 10 minutes prior to delivery.",
        )
        db.session.add(del_detail)

        order_item = OrderItem(
            order_id=order.id,
            listing_id=wheat_listing.id if wheat_listing else None,
            farmer_id=farmer_profile.id,
            produce_name=wheat_listing.name if wheat_listing else "Organic Sharbati Wheat",
            unit_price=Decimal("42.00"),
            unit="kg",
            quantity=Decimal("25.00"),
            subtotal=Decimal("1050.00"),
        )
        db.session.add(order_item)
    click.echo("  [OK] Processed demo order #AGC-2026-8921 with historical price snapshot")

    db.session.commit()
    click.echo("[OK] AgriConnect database successfully seeded!")
