from datetime import datetime, timezone
from app.extensions import db


class Category(db.Model):
    """Product categories for agricultural crops and value-added produce."""
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    listings = db.relationship("ProduceListing", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class ProduceListing(db.Model):
    """Farmer-owned crop harvests listed for direct consumer purchase."""
    __tablename__ = "produce_listings"

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmer_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)  # Fixed-precision currency
    unit = db.Column(db.String(20), nullable=False, default="kg")  # kg, quintal, litre, box
    stock_quantity = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    min_order_quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1.00)
    location = db.Column(db.String(150), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.CheckConstraint("price_per_unit > 0", name="check_positive_price"),
        db.CheckConstraint("stock_quantity >= 0", name="check_non_negative_stock"),
        db.CheckConstraint("min_order_quantity > 0", name="check_positive_min_order"),
    )

    # Relationships
    farmer = db.relationship("FarmerProfile", back_populates="listings")
    category = db.relationship("Category", back_populates="listings")
    cart_items = db.relationship("CartItem", back_populates="listing", cascade="all, delete-orphan")
    order_items = db.relationship("OrderItem", back_populates="listing")

    def __repr__(self) -> str:
        return f"<ProduceListing {self.name} - ₹{self.price_per_unit}/{self.unit}>"


class CartItem(db.Model):
    """Consumer shopping cart items stored persistently."""
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("produce_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1.00)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "listing_id", name="unique_user_cart_listing"),
        db.CheckConstraint("quantity > 0", name="check_positive_cart_qty"),
    )

    user = db.relationship("User", back_populates="cart_items")
    listing = db.relationship("ProduceListing", back_populates="cart_items")

    @property
    def subtotal(self):
        """Computed line subtotal."""
        return self.quantity * self.listing.price_per_unit

    def __repr__(self) -> str:
        return f"<CartItem User:{self.user_id} Listing:{self.listing_id} Qty:{self.quantity}>"
