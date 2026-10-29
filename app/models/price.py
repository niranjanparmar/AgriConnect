import hashlib
from datetime import datetime, timezone
from app.extensions import db


class Crop(db.Model):
    """Agricultural commodity master definition (e.g., Wheat, Cotton, Groundnut)."""
    __tablename__ = "crops"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(60), nullable=True)
    standard_unit = db.Column(db.String(30), nullable=False, default="Quintal (100 kg)")

    # Relationships
    price_records = db.relationship("CropPriceRecord", back_populates="crop", cascade="all, delete-orphan")
    alerts = db.relationship("PriceAlert", back_populates="crop", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Crop {self.name}>"


class Market(db.Model):
    """Regulated APMC wholesale market (Mandi) entity."""
    __tablename__ = "markets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    district = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False, index=True)
    apmc_code = db.Column(db.String(50), unique=True, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("name", "district", "state", name="unique_market_location"),
    )

    # Relationships
    price_records = db.relationship("CropPriceRecord", back_populates="market", cascade="all, delete-orphan")
    alerts = db.relationship("PriceAlert", back_populates="market", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Market {self.name} ({self.district}, {self.state})>"


class CropPriceRecord(db.Model):
    """
    Standardized APMC Mandi daily arrival and modal price records.
    Implements deterministic hashing and constraints to prevent duplicate imports.
    """
    __tablename__ = "crop_price_records"

    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey("crops.id", ondelete="CASCADE"), nullable=False, index=True)
    market_id = db.Column(db.Integer, db.ForeignKey("markets.id", ondelete="CASCADE"), nullable=False, index=True)
    variety = db.Column(db.String(100), nullable=False, default="Common")
    arrival_date = db.Column(db.Date, nullable=False, index=True)
    min_price = db.Column(db.Numeric(10, 2), nullable=False)
    max_price = db.Column(db.Numeric(10, 2), nullable=False)
    modal_price = db.Column(db.Numeric(10, 2), nullable=False)
    arrivals_tonnes = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    source = db.Column(db.String(120), nullable=False, default="Agmarknet")
    record_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.CheckConstraint("min_price >= 0", name="check_min_price_positive"),
        db.CheckConstraint("max_price >= min_price", name="check_max_gte_min"),
        db.CheckConstraint("modal_price >= min_price AND modal_price <= max_price", name="check_modal_within_bounds"),
    )

    crop = db.relationship("Crop", back_populates="price_records")
    market = db.relationship("Market", back_populates="price_records")

    @staticmethod
    def generate_hash(crop_id, market_id, variety, arrival_date) -> str:
        """Create a deterministic SHA-256 fingerprint for idempotent duplicate prevention."""
        key = f"{crop_id}-{market_id}-{variety.strip().lower()}-{arrival_date.isoformat()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def __repr__(self) -> str:
        return f"<CropPriceRecord Crop:{self.crop_id} Market:{self.market_id} Date:{self.arrival_date} Modal:₹{self.modal_price}>"


class PriceAlert(db.Model):
    """User configured rate alerts for specific commodities in selected mandis."""
    __tablename__ = "price_alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_id = db.Column(db.Integer, db.ForeignKey("crops.id", ondelete="CASCADE"), nullable=False, index=True)
    market_id = db.Column(db.Integer, db.ForeignKey("markets.id", ondelete="CASCADE"), nullable=False, index=True)
    target_price = db.Column(db.Numeric(10, 2), nullable=False)
    condition = db.Column(db.String(10), nullable=False, default="Above")  # 'Above' or 'Below'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", back_populates="price_alerts")
    crop = db.relationship("Crop", back_populates="alerts")
    market = db.relationship("Market", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<PriceAlert User:{self.user_id} Crop:{self.crop_id} {self.condition} ₹{self.target_price}>"

