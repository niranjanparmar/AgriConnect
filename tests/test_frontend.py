def test_all_20_required_pages_load_successfully(client):
    """
    Test suite verifying that all 20 required frontend pages and endpoints
    render with HTTP 200 (or expected status codes) and contain core brand elements.
    """
    pages_to_test = [
        # 1. Home
        ("/", 200, b"Fresh Harvest Directly from Farmers"),
        # 2. About
        ("/about", 200, b"Connecting Harvests Directly to Kitchens"),
        # 3. Contact
        ("/contact", 200, b"Get in Touch"),
        # 4 & 5. Farmer and Consumer Registration and Login
        ("/auth/login?role=farmer", 200, b"Farmer"),
        ("/auth/login?role=consumer", 200, b"Consumer"),
        ("/auth/register?role=farmer", 200, b"Choose Account Type"),
        ("/auth/register?role=consumer", 200, b"Consumer"),
        # 6. Farmer Dashboard
        ("/marketplace/farmer/dashboard", 200, b"Farmer Control Center"),
        # 7. Consumer Dashboard
        ("/orders/consumer/dashboard", 200, b"Consumer Dashboard"),
        # 8. Produce Listing Management & Creation
        ("/marketplace/farmer/listings", 200, b"Your Produce Listings"),
        ("/marketplace/farmer/listings/new", 200, b"Farm Produce Listing"),
        # 9. Product Browsing and Search
        ("/marketplace/", 200, b"Direct Agricultural Marketplace"),
        # 10. Product Details
        ("/marketplace/product/1", 200, b"Fresh Harvest In Stock"),
        # 11. Shopping Cart
        ("/orders/cart", 200, b"Your Shopping Cart"),
        # 12. Checkout
        ("/orders/checkout", 200, b"Complete Your Order"),
        # 13. Consumer Order History & Order Details
        ("/orders/history", 200, b"Your Order History"),
        ("/orders/order/8921", 200, b"Live Delivery Progress"),
        # 14. Farmer Order Management
        ("/orders/farmer/orders", 200, b"Inbound Consumer Orders"),
        # 15. Crop Price Tracker
        ("/prices/", 200, b"Agricultural Crop Price Tracker"),
        # 16. Market Comparison
        ("/prices/compare", 200, b"Inter-Mandi Crop Price Comparison"),
        # 17. Historical Price Charts
        ("/prices/trends", 200, b"Historical Crop Price Trends"),
        # 18. Price Alert Management
        ("/prices/alerts", 200, b"Mandi Price Alerts"),
        # 19. User Profile and Settings
        ("/auth/profile", 200, b"Account Profile"),
        # 20. Custom 404 Error State
        ("/this-page-does-not-exist-at-all", 404, b"Page Not Found"),
    ]

    for url, expected_status, expected_text in pages_to_test:
        response = client.get(url)
        assert response.status_code == expected_status, f"Failed for {url}: expected {expected_status}, got {response.status_code}"
        assert expected_text in response.data, f"Failed for {url}: '{expected_text.decode()}' not in response"


def test_marketplace_filtering_and_sorting(client):
    """Test marketplace query string filtering."""
    response = client.get("/marketplace/?q=wheat")
    assert response.status_code == 200
    assert b"Wheat" in response.data

    response = client.get("/marketplace/?category=Fruits")
    assert response.status_code == 200
    assert b"Mangoes" in response.data


def test_price_tracker_filters(client):
    """Test Mandi price tracker filtering."""
    response = client.get("/prices/?crop=Wheat+(Lokwan)")
    assert response.status_code == 200
    assert b"Rajkot APMC" in response.data
