import io
from decimal import Decimal
import pytest
from flask import url_for
from app.extensions import db
from app.models.user import User, FarmerProfile
from app.models.marketplace import Category, ProduceListing
from app.models.order import Order, OrderItem
from app.marketplace.routes import save_listing_image
from werkzeug.datastructures import FileStorage


def test_security_headers_present_on_responses(client):
    """Verify security headers (anti-clickjacking, MIME-sniffing, XSS protection)."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "1; mode=block" in response.headers.get("X-XSS-Protection", "")
    assert "strict-origin-when-cross-origin" in response.headers.get("Referrer-Policy", "")


def test_consumer_denied_farmer_listing_creation(consumer_client):
    """Verify role authorization blocks consumer from farmer produce creation endpoint."""
    response = consumer_client.get("/marketplace/farmer/listings/new")
    assert response.status_code == 403
    assert b"Access Denied" in response.data or b"403" in response.data


def test_farmer_cross_ownership_listing_edit_forbidden(farmer_client, app):
    """Verify farmer cannot edit or tamper with another farmer's produce listings."""
    with app.app_context():
        # Create a second farmer
        other_farmer = User(email="other.farmer@agriconnect.org", full_name="Other Farmer", role="farmer")
        other_farmer.set_password("Pass123!")
        db.session.add(other_farmer)
        db.session.flush()

        other_profile = FarmerProfile(user_id=other_farmer.id, district="Surat", state="Gujarat", is_verified=True)
        db.session.add(other_profile)
        db.session.flush()

        cat = Category.query.first()
        foreign_listing = ProduceListing(
            farmer_id=other_profile.id,
            category_id=cat.id,
            name="Other Farmer Produce",
            price_per_unit=Decimal("50.00"),
            unit="kg",
            stock_quantity=Decimal("100.00"),
            location="Surat",
            description="Owned by other farmer",
        )
        db.session.add(foreign_listing)
        db.session.commit()
        foreign_id = foreign_listing.id

    # Logged-in farmer attempts to edit foreign listing
    response = farmer_client.get(f"/marketplace/farmer/listings/{foreign_id}/edit")
    assert response.status_code == 403


def test_safe_file_upload_rejects_executable_extensions(app):
    """Verify file upload rejects dangerous extensions (.py, .exe, .sh, .php)."""
    with app.app_context():
        # Attempt to upload malicious file
        malicious_file = FileStorage(
            stream=io.BytesIO(b"print('malicious script')"),
            filename="malware.py",
            content_type="text/x-python",
        )
        result = save_listing_image(malicious_file)
        assert result is None


def test_safe_file_upload_sanitizes_path_traversal(app):
    """Verify directory traversal attempts in filenames are stripped cleanly."""
    with app.app_context():
        traversal_file = FileStorage(
            stream=io.BytesIO(b"fake image data"),
            filename="../../../etc/evil_crop.jpg",
            content_type="image/jpeg",
        )
        saved_path = save_listing_image(traversal_file)
        assert saved_path is not None
        assert saved_path.startswith("/static/uploads/listings/")
        # Ensure path traversal components are completely flattened
        assert ".." not in saved_path
        assert "/etc/" not in saved_path
        assert "\\etc\\" not in saved_path
        assert saved_path.endswith("evil_crop.jpg")


def test_safe_file_upload_valid_image(app):
    """Verify legitimate image upload (PNG, JPG) saves with unique prefix and safe path."""
    with app.app_context():
        valid_file = FileStorage(
            stream=io.BytesIO(b"\x89PNG\r\n\x1a\nfake_png_header"),
            filename="fresh_tomatoes.png",
            content_type="image/png",
        )
        saved_path = save_listing_image(valid_file)
        assert saved_path is not None
        assert saved_path.startswith("/static/uploads/listings/")
        assert saved_path.endswith("fresh_tomatoes.png")


def test_sql_injection_defense_in_search(client):
    """Verify SQL injection patterns in search parameters are safely handled as string literals."""
    payload = "Wheat' OR '1'='1"
    response = client.get(f"/marketplace/?q={payload}")
    assert response.status_code == 200
    # Application should treat payload as literal search string, not return arbitrary records


def test_unauthorized_order_tampering_blocked(app, farmer_client, consumer_user):
    """Verify unauthorized users cannot access another consumer's private order receipts."""
    with app.app_context():
        consumer = db.session.get(User, consumer_user.id)
        private_order = Order(
            order_number="AGC-PRIV-999",
            consumer_id=consumer.id,
            total_amount=Decimal("1500.00"),
            status="Confirmed",
        )
        db.session.add(private_order)
        db.session.commit()
        order_id = private_order.id

    # A farmer who does not fulfill items in this order tries to view it
    response = farmer_client.get(f"/orders/order/{order_id}")
    assert response.status_code == 403


def test_error_handlers_do_not_expose_stack_traces(client):
    """Verify error pages return clean, standardized error views without debug traces."""
    res_404 = client.get("/nonexistent-page-url-xyz")
    assert res_404.status_code == 404
    assert b"Page Not Found" in res_404.data
    assert b"Traceback" not in res_404.data
