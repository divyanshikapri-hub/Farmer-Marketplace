from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model mapped to the farmlink_db Users table."""

    __tablename__ = "Users"

    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
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
