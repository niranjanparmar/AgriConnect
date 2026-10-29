from decimal import Decimal
from datetime import date
import pytest
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User, FarmerProfile
from app.models.marketplace import Category, ProduceListing, CartItem
from app.models.order import Order, DeliveryDetail, OrderItem
from app.models.price import Crop, Market, CropPriceRecord, PriceAlert


def test_user_password_hashing(app):
    """Verify passwords are salt-hashed and never stored plaintext."""
    user = User(email="test.hash@agriconnect.local", full_name="Test User", role="farmer")
    user.set_password("MySecurePass123!")

    assert user.password_hash != "MySecurePass123!"
    assert user.check_password("MySecurePass123!") is True
    assert user.check_password("WrongPassword") is False


def test_farmer_profile_relationship(app):
    """Verify 1-to-1 relationship between User and FarmerProfile."""
    farmer = User(email="farmer.test@agriconnect.local", full_name="Farmer Bhai", role="farmer")
    farmer.set_password("pass12345")
    db.session.add(farmer)
    db.session.flush()

    profile = FarmerProfile(
        user_id=farmer.id,
        farm_name="Bhai Farms",
        district="Rajkot",
        state="Gujarat",
        is_verified=True,
    )
    db.session.add(profile)
    db.session.commit()

    retrieved = User.query.filter_by(email="farmer.test@agriconnect.local").first()
    assert retrieved.farmer_profile is not None
    assert retrieved.farmer_profile.farm_name == "Bhai Farms"
    assert retrieved.farmer_profile.user.full_name == "Farmer Bhai"


def test_produce_listing_fixed_precision_and_relationships(app):
    """Verify produce listing stores money as fixed-precision Decimal and relates to category."""
    category = Category(name="Test Grains", slug="test-grains")
    farmer_user = User(email="listing.farmer@agriconnect.local", full_name="Listing Farmer", role="farmer")
    farmer_user.set_password("secret123")
    db.session.add_all([category, farmer_user])
    db.session.flush()

    profile = FarmerProfile(user_id=farmer_user.id, district="Gondal", state="Gujarat")
    db.session.add(profile)
    db.session.flush()

    listing = ProduceListing(
        farmer_id=profile.id,
        category_id=category.id,
        name="Organic Bajra",
        description="Freshly harvested pearl millet",
        price_per_unit=Decimal("38.50"),
        unit="kg",
        stock_quantity=Decimal("500.00"),
        location="Gondal",
    )
    db.session.add(listing)
    db.session.commit()

    saved = ProduceListing.query.filter_by(name="Organic Bajra").first()
    assert isinstance(saved.price_per_unit, Decimal)
    assert saved.price_per_unit == Decimal("38.50")
    assert saved.category.name == "Test Grains"
    assert saved.farmer.user.full_name == "Listing Farmer"


def test_cart_item_uniqueness(app):
    """Verify a consumer cannot have duplicate cart rows for the same listing."""
    user = User(email="cart.user@agriconnect.local", full_name="Cart User", role="consumer")
    user.set_password("pass123")
    cat = Category(name="Produce", slug="produce")
    db.session.add_all([user, cat])
    db.session.flush()

    farmer = User(email="farm.user@agriconnect.local", full_name="Farm User", role="farmer")
    farmer.set_password("pass123")
    db.session.add(farmer)
    db.session.flush()
    profile = FarmerProfile(user_id=farmer.id, district="Rajkot", state="Gujarat")
    db.session.add(profile)
    db.session.flush()

    listing = ProduceListing(
        farmer_id=profile.id,
        category_id=cat.id,
        name="Cart Item Test",
        description="Desc",
        price_per_unit=Decimal("50.00"),
        stock_quantity=Decimal("100.00"),
        location="Rajkot",
    )
    db.session.add(listing)
    db.session.flush()

    item1 = CartItem(user_id=user.id, listing_id=listing.id, quantity=Decimal("5.00"))
    db.session.add(item1)
    db.session.commit()

    # Attempting to add duplicate row for same user + listing should raise IntegrityError
    item2 = CartItem(user_id=user.id, listing_id=listing.id, quantity=Decimal("10.00"))
    db.session.add(item2)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_order_historical_snapshot(app):
    """Verify order items preserve historical prices even if produce listing price changes later."""
    consumer = User(email="buyer@agriconnect.local", full_name="Buyer", role="consumer")
    consumer.set_password("pass")
    cat = Category(name="Spices", slug="spices")
    db.session.add_all([consumer, cat])
    db.session.flush()

    farmer = User(email="spice.grower@agriconnect.local", full_name="Grower", role="farmer")
    farmer.set_password("pass")
    db.session.add(farmer)
    db.session.flush()
    profile = FarmerProfile(user_id=farmer.id, district="Unjha", state="Gujarat")
    db.session.add(profile)
    db.session.flush()

    listing = ProduceListing(
        farmer_id=profile.id,
        category_id=cat.id,
        name="Jeera First Grade",
        description="Cumin",
        price_per_unit=Decimal("300.00"),
        stock_quantity=Decimal("50.00"),
        location="Unjha",
    )
    db.session.add(listing)
    db.session.flush()

    order = Order(
        order_number="AGC-TEST-001",
        consumer_id=consumer.id,
        total_amount=Decimal("650.00"),
        delivery_fee=Decimal("50.00"),
        status="Pending",
    )
    db.session.add(order)
    db.session.flush()

    order_item = OrderItem(
        order_id=order.id,
        listing_id=listing.id,
        farmer_id=profile.id,
        produce_name=listing.name,
        unit_price=listing.price_per_unit,  # 300.00 snapshot
        unit=listing.unit,
        quantity=Decimal("2.00"),
        subtotal=Decimal("600.00"),
    )
    db.session.add(order_item)
    db.session.commit()

    # Farmer now raises price on active market listing to 400.00
    listing.price_per_unit = Decimal("400.00")
    db.session.commit()

    # Past order item snapshot must remain at 300.00
    retrieved_item = OrderItem.query.filter_by(order_id=order.id).first()
    assert retrieved_item.unit_price == Decimal("300.00")
    assert retrieved_item.subtotal == Decimal("600.00")


def test_crop_price_record_idempotency_and_hash(app):
    """Verify deterministic hash prevents duplicate APMC mandi imports."""
    crop = Crop(name="Test Cotton", category="Fiber")
    market = Market(name="Test APMC", district="Amreli", state="Gujarat")
    db.session.add_all([crop, market])
    db.session.commit()

    arrival_dt = date(2026, 10, 28)
    r_hash = CropPriceRecord.generate_hash(crop.id, market.id, "Medium Staple", arrival_dt)

    rec1 = CropPriceRecord(
        crop_id=crop.id,
        market_id=market.id,
        variety="Medium Staple",
        arrival_date=arrival_dt,
        min_price=Decimal("7000.00"),
        max_price=Decimal("7800.00"),
        modal_price=Decimal("7400.00"),
        source="Agmarknet",
        record_hash=r_hash,
    )
    db.session.add(rec1)
    db.session.commit()

    # Inserting the exact same record hash should be prevented by unique constraint
    rec2 = CropPriceRecord(
        crop_id=crop.id,
        market_id=market.id,
        variety="Medium Staple",
        arrival_date=arrival_dt,
        min_price=Decimal("7000.00"),
        max_price=Decimal("7800.00"),
        modal_price=Decimal("7400.00"),
        source="Agmarknet",
        record_hash=r_hash,
    )
    db.session.add(rec2)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()

