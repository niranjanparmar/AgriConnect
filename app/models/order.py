from datetime import datetime, timezone
from app.extensions import db


class Order(db.Model):
    """Consumer placed harvest orders."""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    consumer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_fee = db.Column(db.Numeric(10, 2), nullable=False, default=50.00)
    status = db.Column(db.String(30), nullable=False, default="Pending")  # Pending, Confirmed, Shipped, Delivered, Cancelled
    payment_method = db.Column(db.String(30), nullable=False, default="Cash on Delivery")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    consumer = db.relationship("User", back_populates="orders")
    delivery_detail = db.relationship("DeliveryDetail", back_populates="order", uselist=False, cascade="all, delete-orphan")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order {self.order_number} ({self.status}) - ₹{self.total_amount}>"


class DeliveryDetail(db.Model):
    """Shipping and destination contact details captured for an order."""
    __tablename__ = "delivery_details"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    recipient_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    delivery_instructions = db.Column(db.Text, nullable=True)

    order = db.relationship("Order", back_populates="delivery_detail")

    def __repr__(self) -> str:
        return f"<DeliveryDetail for Order #{self.order_id} - {self.recipient_name}>"


class OrderItem(db.Model):
    """
    Individual items inside an order.
    Maintains a strict historical price and title snapshot so changes to current
    produce listings never alter past completed order receipts.
    """
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("produce_listings.id"), nullable=True, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmer_profiles.id"), nullable=False, index=True)

    # Historical Snapshots
    produce_name = db.Column(db.String(150), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="check_positive_order_qty"),
        db.CheckConstraint("unit_price > 0", name="check_positive_unit_price"),
    )

    # Relationships
    order = db.relationship("Order", back_populates="items")
    listing = db.relationship("ProduceListing", back_populates="order_items")
    farmer = db.relationship("FarmerProfile", back_populates="fulfilled_items")

    def __repr__(self) -> str:
        return f"<OrderItem #{self.id} {self.produce_name} x {self.quantity} = ₹{self.subtotal}>"
