import pytest
from app.extensions import db
from app.models.user import User, FarmerProfile


def test_farmer_registration_success(client):
    """Verify new farmer registration creates User and FarmerProfile in database."""
    response = client.post(
        "/auth/register",
        data={
            "role": "farmer",
            "full_name": "Kishore Solanki",
            "email": "kishore@agriconnect.org",
            "phone": "+91 98980 12345",
            "state": "Gujarat",
            "district": "Gondal",
            "farm_name": "Solanki Oil Orchards",
            "address": "Survey 18, Gondal Yard",
            "pincode": "360311",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Account registered successfully" in response.data

    user = User.query.filter_by(email="kishore@agriconnect.org").first()
    assert user is not None
    assert user.is_farmer is True
    assert user.farmer_profile is not None
    assert user.farmer_profile.district == "Gondal"


def test_registration_duplicate_email_fails(client, farmer_user):
    """Verify registration rejects duplicate email."""
    response = client.post(
        "/auth/register",
        data={
            "role": "consumer",
            "full_name": "Another User",
            "email": farmer_user.email,  # duplicate
            "phone": "+91 99999 88888",
            "state": "Gujarat",
            "district": "Rajkot",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert response.status_code == 200
    assert b"already registered" in response.data


def test_registration_password_mismatch_fails(client):
    """Verify validation catches mismatched passwords."""
    response = client.post(
        "/auth/register",
        data={
            "role": "consumer",
            "full_name": "Test Consumer",
            "email": "mismatch@agriconnect.org",
            "phone": "+91 98989 98989",
            "state": "Gujarat",
            "district": "Rajkot",
            "password": "Password123!",
            "confirm_password": "DifferentPassword123!",
        },
    )
    assert response.status_code == 200
    assert b"Passwords must match" in response.data


def test_login_successful_and_redirects(client, farmer_user):
    """Verify valid login authenticates user and redirects to role dashboard."""
    response = client.post(
        "/auth/login",
        data={
            "email": farmer_user.email,
            "password": "FarmerSecret123!",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Successfully logged in" in response.data
    assert b"Farmer Control Center" in response.data  # Landed on farmer dashboard


def test_login_invalid_password(client, farmer_user):
    """Verify invalid password fails with clear error."""
    response = client.post(
        "/auth/login",
        data={
            "email": farmer_user.email,
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == 200
    assert b"Invalid email address or password" in response.data


def test_protected_route_anonymous_redirect(client):
    """Verify anonymous user cannot access farmer dashboard and is redirected to login."""
    response = client.get("/marketplace/farmer/dashboard")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_role_authorization_consumer_denied_farmer_dashboard(consumer_client):
    """Verify consumer attempting to access farmer portal is rejected with 403 Forbidden."""
    response = consumer_client.get("/marketplace/farmer/dashboard")
    assert response.status_code == 403


def test_logout(farmer_client):
    """Verify logout terminates session."""
    response = farmer_client.get("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"logged out securely" in response.data


def test_profile_update(farmer_client, farmer_user):
    """Verify authenticated user can update profile details."""
    response = farmer_client.post(
        "/auth/profile",
        data={
            "full_name": "Ramesh Patel Updated",
            "phone": "+91 99000 11223",
            "farm_name": "Updated Organic Farms",
            "address": "New Survey 99",
            "district": "Rajkot",
            "state": "Gujarat",
            "pincode": "360005",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Profile information updated successfully" in response.data

    updated = db.session.get(User, farmer_user.id)
    assert updated.full_name == "Ramesh Patel Updated"
    assert updated.farmer_profile.farm_name == "Updated Organic Farms"

