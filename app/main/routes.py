from flask import render_template, request, flash, redirect, url_for
from app.main import main_bp
from app.models.marketplace import ProduceListing
from app.models.price import CropPriceRecord


@main_bp.route("/")
def index():
    # Query active produce listings from database
    featured_products = (
        ProduceListing.query.filter_by(is_active=True)
        .order_by(ProduceListing.created_at.desc())
        .limit(4)
        .all()
    )

    # Query latest mandi crop price records for the live ticker
    recent_prices = (
        CropPriceRecord.query.order_by(CropPriceRecord.arrival_date.desc(), CropPriceRecord.id.desc())
        .limit(4)
        .all()
    )

    price_highlights = []
    for p in recent_prices:
        price_highlights.append({
            "crop": p.crop_name,
            "market": p.market_name,
            "modal_price": int(p.modal_price),
            "unit": "Quintal",
            "change": "+1.5%",
        })

    return render_template("main/index.html", products=featured_products, price_highlights=price_highlights)


@main_bp.route("/about")
def about():
    return render_template("main/about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("All fields are required. Please complete the form before submitting.", "warning")
            return redirect(url_for("main.contact"))

        flash(f"Thank you, {name}! Your message has been received. Our team will contact you at {email}.", "success")
        return redirect(url_for("main.contact"))

    return render_template("main/contact.html")
