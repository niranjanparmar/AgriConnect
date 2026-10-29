from decimal import Decimal
from datetime import date
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User, FarmerProfile
from app.models.marketplace import Category, ProduceListing
from app.models.price import Crop, Market, CropPriceRecord
from app.models.order import Order, DeliveryDetail, OrderItem


@pytest.fixture
def app():
    """Create and configure a clean application instance with minimal seed data."""
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        # Seed minimal categories
        cat_grains = Category(name="Grains & Cereals", slug="grains")
        cat_fruits = Category(name="Fresh Fruits", slug="fruits")
        db.session.add_all([cat_grains, cat_fruits])
        db.session.flush()

        # Seed sample farmer & listing for marketplace tests
        demo_farmer = User(
            email="sample.farmer@agriconnect.org",
            full_name="Ramesh Patel",
            phone="+91 98765 43210",
            role="farmer",
            is_active_account=True,
        )
        demo_farmer.set_password("pass123")
        db.session.add(demo_farmer)
        db.session.flush()

        profile = FarmerProfile(user_id=demo_farmer.id, district="Rajkot", state="Gujarat", is_verified=True)
        db.session.add(profile)
        db.session.flush()

        listing_wheat = ProduceListing(
            farmer_id=profile.id,
            category_id=cat_grains.id,
            name="Fresh Organic Sharbati Wheat",
            description="Premium wheat grain",
            price_per_unit=Decimal("42.00"),
            unit="kg",
            stock_quantity=Decimal("450.00"),
            min_order_quantity=Decimal("5.00"),
            location="Rajkot, Gujarat",
            is_active=True,
        )
        listing_mango = ProduceListing(
            farmer_id=profile.id,
            category_id=cat_fruits.id,
            name="Desi Alphonso Mangoes",
            description="Sweet organic mangoes",
            price_per_unit=Decimal("180.00"),
            unit="kg",
            stock_quantity=Decimal("80.00"),
            min_order_quantity=Decimal("2.00"),
            location="Junagadh, Gujarat",
            is_active=True,
        )
        db.session.add_all([listing_wheat, listing_mango])

        # Seed crop, market, and price record for price tests
        crop = Crop(name="Wheat (Lokwan)", category="Cereal")
        market = Market(name="Rajkot APMC", district="Rajkot", state="Gujarat")
        db.session.add_all([crop, market])
        db.session.flush()

        dt = date(2026, 10, 28)
        r_hash = CropPriceRecord.generate_hash(crop.id, market.id, "Lokwan", dt)
        price_rec = CropPriceRecord(
            crop_id=crop.id,
            market_id=market.id,
            variety="Lokwan",
            arrival_date=dt,
            min_price=Decimal("2600.00"),
            max_price=Decimal("2950.00"),
            modal_price=Decimal("2750.00"),
            arrivals_tonnes=Decimal("140.50"),
            source="Agmarknet",
            record_hash=r_hash,
        )
        db.session.add(price_rec)

        # Seed sample consumer & sample order for order view tests
        sample_consumer = User(
            email="sample.consumer@agriconnect.org",
            full_name="Sample Consumer",
            phone="+91 98250 12345",
            role="consumer",
            is_active_account=True,
        )
        sample_consumer.set_password("pass123")
        db.session.add(sample_consumer)
        db.session.flush()

        sample_order = Order(
            id=8921,
            order_number="AGC-2026-8921",
            consumer_id=sample_consumer.id,
            total_amount=Decimal("1090.00"),
            delivery_fee=Decimal("50.00"),
            status="Confirmed",
        )
        db.session.add(sample_order)
        db.session.flush()

        del_det = DeliveryDetail(
            order_id=sample_order.id,
            recipient_name="Sample Consumer",
            phone="+91 98250 12345",
            address_line="Flat 101, College Road",
            city="Rajkot",
            state="Gujarat",
            pincode="360005",
        )
        ord_item = OrderItem(
            order_id=sample_order.id,
            listing_id=listing_wheat.id,
            farmer_id=profile.id,
            produce_name=listing_wheat.name,
            unit_price=listing_wheat.price_per_unit,
            unit="kg",
            quantity=Decimal("25.00"),
            subtotal=Decimal("1040.00"),
        )
        db.session.add_all([del_det, ord_item])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for issuing requests to the app."""
    return app.test_client()


@pytest.fixture
def farmer_user(app):
    """Seed a verified test farmer user in database."""
    with app.app_context():
        user = User(
            email="test.farmer@agriconnect.org",
            full_name="Ramesh Patel",
            phone="+91 98765 43210",
            role="farmer",
            is_active_account=True,
        )
        user.set_password("FarmerSecret123!")
        db.session.add(user)
        db.session.flush()

        profile = FarmerProfile(
            user_id=user.id,
            farm_name="Patel Farm",
            district="Rajkot",
            state="Gujarat",
            is_verified=True,
        )
        db.session.add(profile)
        db.session.commit()
        db.session.refresh(user)
        db.session.expunge_all()
        return user


@pytest.fixture
def consumer_user(app):
    """Seed a test consumer user in database."""
    with app.app_context():
        user = User(
            email="test.consumer@agriconnect.org",
            full_name="Anand Shah",
            phone="+91 98250 12345",
            role="consumer",
            is_active_account=True,
        )
        user.set_password("ConsumerSecret123!")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        db.session.expunge_all()
        return user


@pytest.fixture
def farmer_client(client, farmer_user):
    """Client logged in as a Farmer."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(farmer_user.id)
        sess["_fresh"] = True
    return client


@pytest.fixture
def consumer_client(client, consumer_user):
    """Client logged in as a Consumer."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(consumer_user.id)
        sess["_fresh"] = True
    return client
