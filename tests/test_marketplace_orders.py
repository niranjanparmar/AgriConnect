from decimal import Decimal
import pytest
from app.extensions import db
from app.models.user import User, FarmerProfile
from app.models.marketplace import Category, ProduceListing, CartItem
from app.models.order import Order, DeliveryDetail, OrderItem


@pytest.fixture
def test_listing(app, farmer_user):
    """Seed an active produce listing with 50 kg stock."""
    with app.app_context():
        farmer = db.session.get(User, farmer_user.id)
        cat = Category.query.first()
        listing = ProduceListing(
            farmer_id=farmer.farmer_profile.id,
            category_id=cat.id,
            name="Organic Gondal Onions",
            description="Sweet red onions",
            price_per_unit=Decimal("35.00"),
            unit="kg",
            stock_quantity=Decimal("50.00"),
            min_order_quantity=Decimal("2.00"),
            location="Gondal, Gujarat",
            is_active=True,
        )
        db.session.add(listing)
        db.session.commit()
        db.session.refresh(listing)
        db.session.expunge_all()
        return listing


def test_add_to_cart_success(consumer_client, test_listing):
    """Verify consumer can add harvest produce to cart within stock limits."""
    response = consumer_client.post(
        "/orders/cart/add",
        data={
            "listing_id": test_listing.id,
            "quantity": 10.0,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Added 10" in response.data

    cart_item = CartItem.query.filter_by(listing_id=test_listing.id).first()
    assert cart_item is not None
    assert cart_item.quantity == Decimal("10.00")


def test_add_to_cart_exceeding_stock_fails(consumer_client, test_listing):
    """Verify adding more than available stock is rejected."""
    response = consumer_client.post(
        "/orders/cart/add",
        data={
            "listing_id": test_listing.id,
            "quantity": 60.0,  # stock is only 50
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Only 50" in response.data


def test_transactional_checkout_and_stock_decrement(consumer_client, consumer_user, test_listing):
    """
    Verify complete checkout process:
    - Creates Order and DeliveryDetail
    - Creates historical OrderItem snapshot
    - Decrements produce listing stock atomically
    - Clears persistent cart
    """
    # 1. Add 10 kg to cart (listing has 50 kg)
    cart_item = CartItem(user_id=consumer_user.id, listing_id=test_listing.id, quantity=Decimal("10.00"))
    db.session.add(cart_item)
    db.session.commit()

    # 2. Checkout
    response = consumer_client.post(
        "/orders/checkout",
        data={
            "recipient_name": "Anand Shah",
            "phone": "+91 98250 12345",
            "address": "Flat 302, Green Park",
            "city": "Rajkot",
            "state": "Gujarat",
            "pincode": "360005",
            "instructions": "Leave with security",
            "payment_method": "Cash on Delivery",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"confirmed! Cash on Delivery order recorded" in response.data

    # 3. Verify stock was safely decremented from 50 to 40
    refreshed_listing = db.session.get(ProduceListing, test_listing.id)
    assert refreshed_listing.stock_quantity == Decimal("40.00")

    # 4. Verify cart was emptied
    remaining_cart = CartItem.query.filter_by(user_id=consumer_user.id).all()
    assert len(remaining_cart) == 0

    # 5. Verify order record & snapshot
    created_order = Order.query.filter_by(consumer_id=consumer_user.id).first()
    assert created_order is not None
    # 10 kg @ 35.00 + 50.00 delivery = 400.00
    assert created_order.total_amount == Decimal("400.00")
    assert len(created_order.items) == 1
    assert created_order.items[0].unit_price == Decimal("35.00")
    assert created_order.items[0].produce_name == "Organic Gondal Onions"


def test_insufficient_stock_rollback_at_checkout(consumer_client, consumer_user, test_listing):
    """Verify that if stock becomes insufficient before checkout, transaction rolls back."""
    # Consumer placed 10 kg in cart
    cart_item = CartItem(user_id=consumer_user.id, listing_id=test_listing.id, quantity=Decimal("10.00"))
    db.session.add(cart_item)
    db.session.commit()

    # Meanwhile, another consumer bought remaining stock, leaving only 5 kg
    listing_to_update = db.session.get(ProduceListing, test_listing.id)
    listing_to_update.stock_quantity = Decimal("5.00")
    db.session.commit()

    # Now consumer attempts checkout with 10 kg in cart
    response = consumer_client.post(
        "/orders/checkout",
        data={
            "recipient_name": "Anand Shah",
            "phone": "+91 98250 12345",
            "address": "Flat 302, Green Park",
            "city": "Rajkot",
            "state": "Gujarat",
            "pincode": "360005",
            "payment_method": "Cash on Delivery",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Insufficient stock" in response.data

    # Stock should remain at 5.00 and no new order should be created
    refreshed = db.session.get(ProduceListing, test_listing.id)
    assert refreshed.stock_quantity == Decimal("5.00")


def test_unauthorized_order_view_forbidden(app, test_listing):
    """Verify a consumer cannot view another consumer's order (HTTP 403)."""
    with app.app_context():
        # Create Owner Consumer
        owner = User(email="owner@agriconnect.org", full_name="Owner", role="consumer")
        owner.set_password("pass123")
        # Create Hacker Consumer
        intruder = User(email="intruder@agriconnect.org", full_name="Intruder", role="consumer")
        intruder.set_password("pass123")
        db.session.add_all([owner, intruder])
        db.session.flush()

        order = Order(
            order_number="AGC-SEC-001",
            consumer_id=owner.id,
            total_amount=Decimal("100.00"),
            status="Pending",
        )
        db.session.add(order)
        db.session.commit()
        order_id = order.id
        intruder_id = intruder.id

    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["_user_id"] = str(intruder_id)
        sess["_fresh"] = True

    response = test_client.get(f"/orders/order/{order_id}")
    assert response.status_code == 403


def test_farmer_order_status_update(farmer_client, farmer_user, test_listing):
    """Verify fulfilling farmer can transition order status."""
    farmer = db.session.get(User, farmer_user.id)
    consumer = User(email="c.buyer@agriconnect.org", full_name="Buyer", role="consumer")
    consumer.set_password("pass")
    db.session.add(consumer)
    db.session.flush()

    order = Order(order_number="AGC-STATUS-101", consumer_id=consumer.id, total_amount=Decimal("200.00"), status="Pending")
    db.session.add(order)
    db.session.flush()

    item = OrderItem(
        order_id=order.id,
        listing_id=test_listing.id,
        farmer_id=farmer.farmer_profile.id,
        produce_name=test_listing.name,
        unit_price=Decimal("35.00"),
        unit="kg",
        quantity=Decimal("5.00"),
        subtotal=Decimal("175.00"),
    )
    db.session.add(item)
    db.session.commit()

    # Farmer transitions status from Pending to Confirmed
    response = farmer_client.post(
        "/orders/farmer/orders",
        data={
            "order_id": order.id,
            "status": "Confirmed",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"status updated to" in response.data and b"Confirmed" in response.data

    updated = db.session.get(Order, order.id)
    assert updated.status == "Confirmed"
