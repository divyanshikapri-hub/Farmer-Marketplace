from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model mapped to the farmlink_db Users table."""

    __tablename__ = "Users"

    user_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum("farmer", "buyer", "transporter", "admin", name="user_roles"),
        nullable=False,
        default="buyer",
    )
    status = db.Column(
        db.Enum("active", "inactive", "suspended", name="user_statuses"),
        nullable=False,
        default="active",
    )
    address_line = db.Column(db.Text, nullable=True)  # Village / Street address
    city = db.Column(db.String(100), nullable=False)   # District / City
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False, default="000000")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def set_password(self, password: str) -> None:
        """Hash and set the user password using Werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against stored Werkzeug hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Serialize user model to a dictionary representation."""
        return {
            "user_id": self.user_id,
            "name": self.full_name,
            "email": self.email,
            "phone": self.phone_number,
            "role": self.role,
            "status": self.status,
            "village": self.address_line,
            "district": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Crop(db.Model):
    """Crop model mapped to the farmlink_db Crops table."""

    __tablename__ = "Crops"

    crop_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    farmer_id = db.Column(
        db.BigInteger,
        db.ForeignKey("Users.user_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    crop_name = db.Column(db.String(100), nullable=False)
    category = db.Column(
        db.Enum(
            "grain", "vegetable", "fruit", "pulse", "oilseed", "other",
            name="crop_categories"
        ),
        nullable=False,
        default="vegetable",
    )
    quantity_available = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(
        db.Enum("kg", "ton", "quintal", "box", "bag", name="crop_units"),
        nullable=False,
        default="kg",
    )
    price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    harvest_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum("available", "reserved", "sold_out", "archived", name="crop_statuses"),
        nullable=False,
        default="available",
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    farmer = db.relationship("User", backref=db.backref("crops", lazy=True))

    def to_dict(self, include_farmer: bool = False) -> dict:
        """Serialize crop model to dictionary representation."""
        data = {
            "crop_id": self.crop_id,
            "farmer_id": self.farmer_id,
            "crop_name": self.crop_name,
            "category": self.category,
            "quantity_available": (
                float(self.quantity_available)
                if self.quantity_available is not None
                else 0.0
            ),
            "unit": self.unit,
            "price_per_unit": (
                float(self.price_per_unit)
                if self.price_per_unit is not None
                else 0.0
            ),
            "harvest_date": (
                self.harvest_date.isoformat()
                if self.harvest_date
                else None
            ),
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if self.farmer:
            data["farmer_name"] = self.farmer.full_name
            data["farmer_village"] = self.farmer.address_line
            data["farmer_district"] = self.farmer.city
            data["farmer_state"] = self.farmer.state
            if include_farmer:
                data["farmer"] = {
                    "user_id": self.farmer.user_id,
                    "name": self.farmer.full_name,
                    "email": self.farmer.email,
                    "phone": self.farmer.phone_number,
                    "village": self.farmer.address_line,
                    "district": self.farmer.city,
                    "state": self.farmer.state,
                }

        return data


class Order(db.Model):
    """Order model mapped to the farmlink_db Orders table."""

    __tablename__ = "Orders"

    order_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    buyer_id = db.Column(
        db.BigInteger,
        db.ForeignKey("Users.user_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    shipping_address = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.Enum(
            "pending",
            "placed",
            "confirmed",
            "processing",
            "shipped",
            "delivered",
            "cancelled",
            name="order_statuses",
        ),
        nullable=False,
        default="placed",
    )
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    buyer = db.relationship("User", backref=db.backref("orders", lazy=True))
    items = db.relationship(
        "OrderItem",
        backref="order",
        cascade="all, delete-orphan",
        lazy=True,
    )
    payment = db.relationship(
        "Payment",
        backref="order",
        uselist=False,
        cascade="all, delete-orphan",
        lazy=True,
    )
    delivery = db.relationship(
        "Delivery",
        backref="order",
        uselist=False,
        cascade="all, delete-orphan",
        lazy=True,
    )

    def to_dict(self, include_relations: bool = True) -> dict:
        """Serialize order model to dictionary representation."""
        data = {
            "order_id": self.order_id,
            "buyer_id": self.buyer_id,
            "buyer_name": self.buyer.full_name if self.buyer else None,
            "total_amount": (
                float(self.total_amount)
                if self.total_amount is not None
                else 0.0
            ),
            "shipping_address": self.shipping_address,
            "status": self.status,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_relations:
            data["items"] = [item.to_dict() for item in self.items] if self.items else []
            data["payment"] = self.payment.to_dict() if self.payment else None
            data["delivery"] = self.delivery.to_dict() if self.delivery else None
        return data


class OrderItem(db.Model):
    """OrderItem model mapped to the farmlink_db OrderItems table."""

    __tablename__ = "OrderItems"

    order_item_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("Orders.order_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    crop_id = db.Column(
        db.BigInteger,
        db.ForeignKey("Crops.crop_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    crop = db.relationship("Crop", backref=db.backref("order_items", lazy=True))

    def to_dict(self) -> dict:
        """Serialize order item model to dictionary representation."""
        return {
            "order_item_id": self.order_item_id,
            "order_id": self.order_id,
            "crop_id": self.crop_id,
            "crop_name": self.crop.crop_name if self.crop else None,
            "unit": self.crop.unit if self.crop else "kg",
            "quantity": float(self.quantity) if self.quantity is not None else 0.0,
            "unit_price": float(self.unit_price) if self.unit_price is not None else 0.0,
            "subtotal": float(self.subtotal) if self.subtotal is not None else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Payment(db.Model):
    """Payment model mapped to the farmlink_db Payments table."""

    __tablename__ = "Payments"

    payment_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("Orders.order_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_method = db.Column(
        db.Enum(
            "card",
            "netbanking",
            "bank_transfer",
            "upi",
            "mobile_money",
            "cash_on_delivery",
            "cod",
            name="payment_methods",
        ),
        nullable=False,
    )
    status = db.Column(
        db.Enum(
            "pending", "completed", "failed", "refunded",
            name="payment_statuses"
        ),
        nullable=False,
        default="pending",
    )
    transaction_reference = db.Column(
        db.String(100), unique=True, nullable=False, index=True
    )
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        """Serialize payment model to dictionary representation."""
        return {
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "amount": float(self.amount) if self.amount is not None else 0.0,
            "payment_method": self.payment_method,
            "status": self.status,
            "transaction_reference": self.transaction_reference,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Delivery(db.Model):
    """Delivery model mapped to the farmlink_db Deliveries table."""

    __tablename__ = "Deliveries"

    delivery_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    order_id = db.Column(
        db.BigInteger,
        db.ForeignKey("Orders.order_id", ondelete="CASCADE", onupdate="CASCADE"),
        unique=True,
        nullable=False,
    )
    transporter_id = db.Column(
        db.BigInteger,
        db.ForeignKey("Users.user_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    pickup_address = db.Column(db.Text, nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    tracking_number = db.Column(
        db.String(100), unique=True, nullable=False, index=True
    )
    status = db.Column(
        db.Enum(
            "pending",
            "assigned",
            "picked_up",
            "in_transit",
            "delivered",
            "failed",
            "cancelled",
            name="delivery_statuses",
        ),
        nullable=False,
        default="pending",
    )
    estimated_delivery = db.Column(db.DateTime, nullable=True)
    actual_delivery = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    transporter = db.relationship(
        "User",
        foreign_keys=[transporter_id],
        backref=db.backref("assigned_deliveries", lazy=True),
    )

    def to_dict(self) -> dict:
        """Serialize delivery model to dictionary representation."""
        return {
            "delivery_id": self.delivery_id,
            "order_id": self.order_id,
            "transporter_id": self.transporter_id,
            "transporter_name": self.transporter.full_name if self.transporter else None,
            "transporter_phone": self.transporter.phone_number if self.transporter else None,
            "pickup_address": self.pickup_address,
            "delivery_address": self.delivery_address,
            "tracking_number": self.tracking_number,
            "status": self.status,
            "estimated_delivery": (
                self.estimated_delivery.isoformat()
                if self.estimated_delivery
                else None
            ),
            "actual_delivery": (
                self.actual_delivery.isoformat()
                if self.actual_delivery
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


