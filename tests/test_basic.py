def test_app_creation(app):
    """Verify application initializes in testing mode."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_home_page_loads(client):
    """Verify the home page route responds with HTTP 200 and expected brand."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"AgriConnect" in response.data


def test_about_page_loads(client):
    """Verify about page loads correctly."""
    response = client.get("/about")
    assert response.status_code == 200
    assert b"About Us" in response.data


def test_contact_page_loads(client):
    """Verify contact page loads correctly."""
    response = client.get("/contact")
    assert response.status_code == 200
    assert b"Get in Touch" in response.data


def test_404_error_handler(client):
    """Verify custom 404 handler functions properly."""
    response = client.get("/non-existent-page-url")
    assert response.status_code == 404
    assert b"404" in response.data

