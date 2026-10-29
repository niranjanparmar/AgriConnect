import pytest
from app import create_app
from app.extensions import db


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
def runner(app):
    """Test CLI runner for invoking Flask CLI commands."""
    return app.test_cli_runner()
