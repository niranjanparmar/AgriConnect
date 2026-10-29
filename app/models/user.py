from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    """Core user account supporting Role-Based Access Control (Farmer vs Consumer)."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="consumer")  # 'farmer' or 'consumer' or 'admin'
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    farmer_profile = db.relationship("FarmerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="consumer", cascade="all, delete-orphan")
    cart_items = db.relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    price_alerts = db.relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Securely hash and store password using Werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify plain password against stored salt-and-hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_farmer(self) -> bool:
        return self.role.lower() == "farmer"

    @property
    def is_consumer(self) -> bool:
        return self.role.lower() == "consumer"

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


class FarmerProfile(db.Model):
    """Detailed agricultural profile linked 1-to-1 with a Farmer User."""
    __tablename__ = "farmer_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    farm_name = db.Column(db.String(150), nullable=True)
    farm_address = db.Column(db.Text, nullable=True)
    district = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="farmer_profile")
    listings = db.relationship("ProduceListing", back_populates="farmer", cascade="all, delete-orphan")
    fulfilled_items = db.relationship("OrderItem", back_populates="farmer")

    def __repr__(self) -> str:
        return f"<FarmerProfile {self.farm_name or self.user.full_name} ({self.district}, {self.state})>"
