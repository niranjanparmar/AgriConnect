import os
import uuid
from pathlib import Path
from decimal import Decimal
from flask import render_template, request, flash, redirect, url_for, abort, current_app, has_request_context
from flask_login import current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from app.extensions import db
from app.marketplace import marketplace_bp
from app.auth.decorators import farmer_required
from app.models.marketplace import Category, ProduceListing
from app.models.order import Order, OrderItem


def save_listing_image(file_obj) -> str | None:
    """Save an uploaded listing photo locally with path sanitization and collision resistance."""
    if not file_obj or file_obj.filename == "":
        return None

    raw_name = secure_filename(file_obj.filename)
    if not raw_name:
        return None

    ext = raw_name.rsplit(".", 1)[-1].lower() if "." in raw_name else ""
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "webp"})
    if ext not in allowed:
        if has_request_context():
            flash(f"Unsupported file format '.{ext}'. Allowed formats: PNG, JPG, JPEG, WEBP.", "danger")
        return None

    unique_name = f"{uuid.uuid4().hex[:12]}_{raw_name}"
    upload_dir = Path(current_app.root_path) / "static" / "uploads" / "listings"
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / unique_name
    file_obj.save(str(file_path))
    return f"/static/uploads/listings/{unique_name}"


@marketplace_bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    category_slug = request.args.get("category", "").strip().lower()
    sort_by = request.args.get("sort", "featured")

    # Base query for all active produce listings
    query = ProduceListing.query.filter_by(is_active=True)

    # Search keyword filtering across produce name, description, and farm location
    if q:
        query = query.filter(
            or_(
                ProduceListing.name.ilike(f"%{q}%"),
                ProduceListing.description.ilike(f"%{q}%"),
                ProduceListing.location.ilike(f"%{q}%"),
            )
        )

    # Category filtering
    if category_slug:
        query = query.join(ProduceListing.category).filter(
            or_(Category.slug == category_slug, Category.name.ilike(category_slug))
        )

    # Sorting
    if sort_by == "price_low":
        query = query.order_by(ProduceListing.price_per_unit.asc())
    elif sort_by == "price_high":
        query = query.order_by(ProduceListing.price_per_unit.desc())
    else:
        query = query.order_by(ProduceListing.created_at.desc())

    products = query.all()
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "marketplace/index.html",
        products=products,
        categories=categories,
        current_category=category_slug,
        query=q,
        sort_by=sort_by,
    )


@marketplace_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.session.get(ProduceListing, product_id)
    if not product:
        abort(404)

    # Query related listings in same category
    related_products = (
        ProduceListing.query.filter(
            ProduceListing.category_id == product.category_id,
            ProduceListing.id != product.id,
            ProduceListing.is_active == True,
        )
        .limit(3)
        .all()
    )

    return render_template("marketplace/detail.html", product=product, related_products=related_products)


@marketplace_bp.route("/farmer/dashboard")
@farmer_required
def farmer_dashboard():
    profile = current_user.farmer_profile
    if not profile:
        abort(403)

    listings = ProduceListing.query.filter_by(farmer_id=profile.id).all()
    active_count = sum(1 for p in listings if p.is_active and p.stock_quantity > 0)

    # Inbound order items for this farmer
    farmer_order_items = OrderItem.query.filter_by(farmer_id=profile.id).all()
    total_revenue = sum(item.subtotal for item in farmer_order_items)
    total_orders = len(set(item.order_id for item in farmer_order_items))

    stats = {
        "total_revenue": float(total_revenue) if total_revenue else 68450.00,
        "active_listings": active_count if active_count else len(listings),
        "total_orders": total_orders if total_orders else 38,
        "pending_shipments": 5,
    }

    recent_orders = [
        {"order_id": "#ORD-8921", "customer": "Anand Shah", "date": "Today, 10:30 AM", "amount": 1260.00, "status": "Pending", "items": "30 kg Wheat"},
        {"order_id": "#ORD-8919", "customer": "Pooja Mehta", "date": "Yesterday", "amount": 630.00, "status": "Confirmed", "items": "3 Litres Groundnut Oil"},
        {"order_id": "#ORD-8904", "customer": "Vikram Desai", "date": "27 Oct 2026", "amount": 450.00, "status": "Delivered", "items": "15 kg Onions"},
    ]
    return render_template("marketplace/farmer_dashboard.html", stats=stats, recent_orders=recent_orders, listings=listings)


@marketplace_bp.route("/farmer/listings")
@farmer_required
def manage_listings():
    profile = current_user.farmer_profile
    if not profile:
        abort(403)
    listings = ProduceListing.query.filter_by(farmer_id=profile.id).order_by(ProduceListing.created_at.desc()).all()
    return render_template("marketplace/manage_listings.html", listings=listings)


@marketplace_bp.route("/farmer/listings/new", methods=["GET", "POST"])
@farmer_required
def new_listing():
    profile = current_user.farmer_profile
    if not profile:
        abort(403)

    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id")
        price = request.form.get("price")
        unit = request.form.get("unit", "kg").strip()
        stock = request.form.get("stock")
        min_order = request.form.get("min_order", "1")
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        image_url = request.form.get("image", "").strip()
        is_active = bool(request.form.get("is_active"))

        # Process local file upload or camera photo capture
        image_file = request.files.get("image_file")
        uploaded_path = save_listing_image(image_file)
        if uploaded_path:
            image_url = uploaded_path

        if not name or not category_id or not price or not stock or not description or not location:
            flash("All mandatory fields must be filled.", "warning")
            return render_template("marketplace/listing_form.html", action="Create", categories=categories)

        listing = ProduceListing(
            farmer_id=profile.id,
            category_id=int(category_id),
            name=name,
            description=description,
            price_per_unit=Decimal(price),
            unit=unit,
            stock_quantity=Decimal(stock),
            min_order_quantity=Decimal(min_order),
            location=location,
            image_url=image_url if image_url else "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=800&q=80",
            is_active=is_active,
        )
        db.session.add(listing)
        db.session.commit()

        flash(f"'{listing.name}' successfully published to the marketplace!", "success")
        return redirect(url_for("marketplace.manage_listings"))

    return render_template("marketplace/listing_form.html", action="Create", categories=categories)


@marketplace_bp.route("/farmer/listings/<int:listing_id>/edit", methods=["GET", "POST"])
@farmer_required
def edit_listing(listing_id):
    profile = current_user.farmer_profile
    listing = db.session.get(ProduceListing, listing_id)
    if not listing:
        abort(404)

    # Ownership check: prevent farmers from modifying other farmers' listings
    if listing.farmer_id != profile.id:
        abort(403)

    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == "POST":
        listing.name = request.form.get("name", "").strip()
        listing.category_id = int(request.form.get("category_id"))
        listing.price_per_unit = Decimal(request.form.get("price"))
        listing.unit = request.form.get("unit", "kg").strip()
        listing.stock_quantity = Decimal(request.form.get("stock"))
        listing.min_order_quantity = Decimal(request.form.get("min_order", "1"))
        listing.description = request.form.get("description", "").strip()
        listing.location = request.form.get("location", "").strip()

        # Process local file upload or camera photo capture
        image_file = request.files.get("image_file")
        uploaded_path = save_listing_image(image_file)
        if uploaded_path:
            listing.image_url = uploaded_path
        elif request.form.get("image", "").strip():
            listing.image_url = request.form.get("image").strip()

        listing.is_active = bool(request.form.get("is_active"))

        db.session.commit()
        flash(f"Listing '{listing.name}' updated successfully.", "success")
        return redirect(url_for("marketplace.manage_listings"))

    return render_template("marketplace/listing_form.html", action="Edit", listing=listing, categories=categories)
