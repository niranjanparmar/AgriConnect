import pytest
from app import create_app
from app.extensions import db
from app.models.user import User, FarmerProfile


@pytest.fixture
def app():
    """Create and configure a clean application instance for testing."""
    app = create_app("testing")

    with app.app_context():
        db.create_all()
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
