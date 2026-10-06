from functools import wraps
from flask import Blueprint, request, jsonify, session
from models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


def login_required(f):
    """Decorator to enforce authenticated session on protected routes."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return (
                jsonify(
                    {
                        "error": "Unauthorized",
                        "message": "Authentication required. Please log in.",
                    }
                ),
                401,
            )
        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /api/register
    Accepts: name, email, password, role, phone, village, district, state, (optional postal_code)
    Hashes password using Werkzeug security before persisting to the database.
    """
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Invalid JSON payload or missing Content-Type application/json.",
                }
            ),
            400,
        )

    # Extract required fields with flexible key aliases
    name = (data.get("name") or data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    phone = (data.get("phone") or data.get("phone_number") or "").strip()
    role = (data.get("role") or "buyer").strip().lower()
    village = (data.get("village") or data.get("address_line") or "").strip()
    district = (data.get("district") or data.get("city") or "").strip()
    state = (data.get("state") or "").strip()
    postal_code = (data.get("postal_code") or "000000").strip()

    # Field validations
    missing_fields = []
    if not name:
        missing_fields.append("name")
    if not email:
        missing_fields.append("email")
    if not password:
        missing_fields.append("password")
    if not phone:
        missing_fields.append("phone")
    if not district:
        missing_fields.append("district")
    if not state:
        missing_fields.append("state")

    if missing_fields:
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}",
                }
            ),
            400,
        )

    # Role validation against schema ENUM
    allowed_roles = {"farmer", "buyer", "transporter", "admin"}
    if role not in allowed_roles:
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": f"Invalid role '{role}'. Allowed roles: {', '.join(allowed_roles)}.",
                }
            ),
            400,
        )

    if len(password) < 6:
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": "Password must be at least 6 characters long.",
                }
            ),
            400,
        )

    # Check for existing email or phone
    existing_user = User.query.filter(
        (User.email == email) | (User.phone_number == phone)
    ).first()

    if existing_user:
        conflict_field = "Email" if existing_user.email == email else "Phone number"
        return (
            jsonify(
                {
                    "error": "Conflict",
                    "message": f"{conflict_field} is already registered.",
                }
            ),
            409,
        )

    # Create new User instance with hashed password
    new_user = User(
        full_name=name,
        email=email,
        phone_number=phone,
        role=role,
        status="active",
        address_line=village,
        city=district,
        state=state,
        postal_code=postal_code,
    )
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": f"Failed to register user: {str(e)}",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "message": "User registered successfully.",
                "user": new_user.to_dict(),
            }
        ),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/login
    Accepts: email (or phone), password
    Validates credentials, checks password hash, and stores user session.
    """
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Invalid JSON payload or missing Content-Type application/json.",
                }
            ),
            400,
        )

    identifier = (data.get("email") or data.get("phone") or "").strip().lower()
    password = data.get("password") or ""

    if not identifier or not password:
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": "Both email/phone and password are required.",
                }
            ),
            400,
        )

    # Allow login with either email or phone number
    user = User.query.filter(
        (User.email == identifier) | (User.phone_number == identifier)
    ).first()

    if not user or not user.check_password(password):
        return (
            jsonify(
                {
                    "error": "Unauthorized",
                    "message": "Invalid credentials. Please verify your email/phone and password.",
                }
            ),
            401,
        )

    if user.status != "active":
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": f"Account is {user.status}. Please contact support.",
                }
            ),
            403,
        )

    # Store user identity in flask.session
    session.clear()
    session["user_id"] = user.user_id
    session["role"] = user.role
    session["name"] = user.full_name

    return (
        jsonify(
            {
                "message": "Login successful.",
                "user": user.to_dict(),
                "session": {
                    "user_id": session["user_id"],
                    "role": session["role"],
                    "name": session["name"],
                },
            }
        ),
        200,
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    POST /api/logout
    Clears active user session.
    """
    session.clear()
    return (
        jsonify(
            {
                "message": "Logout successful. Session cleared.",
            }
        ),
        200,
    )


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """
    GET /api/me
    Returns current authenticated user details from session and database.
    Protected by @login_required.
    """
    user_id = session.get("user_id")
    user = User.query.get(user_id)

    if not user:
        session.clear()
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": "User associated with this session no longer exists.",
                }
            ),
            404,
        )

    return (
        jsonify(
            {
                "user": user.to_dict(),
                "session": {
                    "user_id": session.get("user_id"),
                    "role": session.get("role"),
                    "name": session.get("name"),
                },
            }
        ),
        200,
    )
