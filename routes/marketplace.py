from datetime import datetime
from decimal import Decimal
from functools import wraps
import uuid

from flask import Blueprint, request, jsonify, session
from models import db, Crop, Order, OrderItem, Payment, Delivery, User
from auth import login_required

marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/api")

# Allowed constants matching database schema enums
ALLOWED_CROP_CATEGORIES = {"grain", "vegetable", "fruit", "pulse", "oilseed", "other"}
ALLOWED_CROP_UNITS = {"kg", "ton", "quintal", "box", "bag"}
ALLOWED_CROP_STATUSES = {"available", "reserved", "sold_out", "archived"}
ALLOWED_PAYMENT_METHODS = {
    "card",
    "netbanking",
    "bank_transfer",
    "upi",
    "mobile_money",
    "cash_on_delivery",
    "cod",
}
ALLOWED_DELIVERY_STATUSES = {
    "pending",
    "assigned",
    "picked_up",
    "in_transit",
    "delivered",
    "failed",
    "cancelled",
}


def roles_required(*allowed_roles):
    """
    Decorator to enforce Role-Based Access Control (RBAC).
    Ensures active user session and role membership (admin always permitted).
    """

    def decorator(f):
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
            user_role = session.get("role")
            if user_role not in allowed_roles and user_role != "admin":
                return (
                    jsonify(
                        {
                            "error": "Forbidden",
                            "message": (
                                f"Access denied. Requires one of roles: "
                                f"{', '.join(allowed_roles)} (current role: '{user_role}')."
                            ),
                        }
                    ),
                    403,
                )
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# =============================================================================
# 1. CROPS / INVENTORY ENDPOINTS (/api/crops)
# =============================================================================


@marketplace_bp.route("/crops", methods=["GET"])
def get_crops():
    """
    GET /api/crops
    List all active/available crops with optional filters:
      - category: filter by crop category ('grain', 'vegetable', etc.)
      - search: filter by name or description (case-insensitive substring)
      - min_price: filter crops with price_per_unit >= min_price
      - max_price: filter crops with price_per_unit <= max_price
      - status: override default 'available' filter (use 'all' for any status)
      - farmer_id: filter crops listed by specific farmer
    """
    query = Crop.query

    # Status filtering (default to 'available')
    status_filter = request.args.get("status")
    if status_filter:
        if status_filter.lower() != "all":
            query = query.filter(Crop.status == status_filter)
    else:
        query = query.filter(Crop.status == "available")

    # Category filter
    category = request.args.get("category")
    if category:
        query = query.filter(Crop.category == category.lower())

    # Farmer ID filter
    farmer_id = request.args.get("farmer_id")
    if farmer_id:
        try:
            query = query.filter(Crop.farmer_id == int(farmer_id))
        except ValueError:
            pass

    # Search keyword filter (by name or description)
    search = request.args.get("search")
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            Crop.crop_name.ilike(search_term) | Crop.description.ilike(search_term)
        )

    # Price range filters
    min_price = request.args.get("min_price")
    if min_price:
        try:
            min_val = float(min_price)
            query = query.filter(Crop.price_per_unit >= min_val)
        except ValueError:
            return (
                jsonify(
                    {
                        "error": "Validation Error",
                        "message": "min_price must be a valid number.",
                    }
                ),
                400,
            )

    max_price = request.args.get("max_price")
    if max_price:
        try:
            max_val = float(max_price)
            query = query.filter(Crop.price_per_unit <= max_val)
        except ValueError:
            return (
                jsonify(
                    {
                        "error": "Validation Error",
                        "message": "max_price must be a valid number.",
                    }
                ),
                400,
            )

    crops = query.order_by(Crop.created_at.desc()).all()
    return (
        jsonify(
            {
                "count": len(crops),
                "crops": [crop.to_dict(include_farmer=True) for crop in crops],
            }
        ),
        200,
    )


@marketplace_bp.route("/crops/<int:crop_id>", methods=["GET"])
def get_crop(crop_id):
    """
    GET /api/crops/<crop_id>
    Retrieve single crop details including farmer name, village, state, and phone.
    """
    crop = db.session.get(Crop, crop_id)
    if not crop:
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": f"Crop with ID {crop_id} was not found.",
                }
            ),
            404,
        )

    return jsonify({"crop": crop.to_dict(include_farmer=True)}), 200


@marketplace_bp.route("/crops", methods=["POST"])
@roles_required("farmer")
def create_crop():
    """
    POST /api/crops
    (@login_required, role='farmer' or 'admin')
    Add a new crop listing linked to the authenticated session user.
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

    crop_name = (data.get("crop_name") or data.get("name") or "").strip()
    category = (data.get("category") or "vegetable").strip().lower()
    unit = (data.get("unit") or "kg").strip().lower()
    description = (data.get("description") or "").strip()
    harvest_date_str = (data.get("harvest_date") or "").strip()
    status = (data.get("status") or "available").strip().lower()

    # Numeric fields
    raw_qty = data.get("quantity_available") or data.get("quantity")
    raw_price = data.get("price_per_unit") or data.get("price")

    missing_fields = []
    if not crop_name:
        missing_fields.append("crop_name")
    if raw_qty is None:
        missing_fields.append("quantity_available")
    if raw_price is None:
        missing_fields.append("price_per_unit")

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

    # Validate numbers
    try:
        quantity = Decimal(str(raw_qty))
        if quantity <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": "quantity_available must be a positive number greater than 0.",
                }
            ),
            400,
        )

    try:
        price = Decimal(str(raw_price))
        if price <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": "price_per_unit must be a positive number greater than 0.",
                }
            ),
            400,
        )

    if category not in ALLOWED_CROP_CATEGORIES:
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": (
                        f"Invalid category '{category}'. Allowed: "
                        f"{', '.join(ALLOWED_CROP_CATEGORIES)}"
                    ),
                }
            ),
            400,
        )

    if unit not in ALLOWED_CROP_UNITS:
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": f"Invalid unit '{unit}'. Allowed: {', '.join(ALLOWED_CROP_UNITS)}",
                }
            ),
            400,
        )

    if status not in ALLOWED_CROP_STATUSES:
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": (
                        f"Invalid status '{status}'. Allowed: "
                        f"{', '.join(ALLOWED_CROP_STATUSES)}"
                    ),
                }
            ),
            400,
        )

    harvest_date = None
    if harvest_date_str:
        try:
            harvest_date = datetime.strptime(harvest_date_str, "%Y-%m-%d").date()
        except ValueError:
            return (
                jsonify(
                    {
                        "error": "Validation Error",
                        "message": "harvest_date must be in YYYY-MM-DD format.",
                    }
                ),
                400,
            )

    farmer_id = session["user_id"]

    new_crop = Crop(
        farmer_id=farmer_id,
        crop_name=crop_name,
        category=category,
        quantity_available=quantity,
        unit=unit,
        price_per_unit=price,
        harvest_date=harvest_date,
        description=description if description else None,
        status=status,
    )

    try:
        db.session.add(new_crop)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": f"Failed to list crop: {str(e)}",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "message": "Crop listing created successfully.",
                "crop": new_crop.to_dict(include_farmer=True),
            }
        ),
        201,
    )


@marketplace_bp.route("/crops/<int:crop_id>", methods=["PUT"])
@roles_required("farmer")
def update_crop(crop_id):
    """
    PUT /api/crops/<crop_id>
    (@login_required, role='farmer' or 'admin')
    Update price, available quantity, or status.
    Ensures only the owner farmer (or admin) can edit.
    """
    crop = db.session.get(Crop, crop_id)
    if not crop:
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": f"Crop with ID {crop_id} was not found.",
                }
            ),
            404,
        )

    # Ownership check
    current_user_id = session.get("user_id")
    current_role = session.get("role")
    if crop.farmer_id != current_user_id and current_role != "admin":
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "You do not have permission to modify this crop listing.",
                }
            ),
            403,
        )

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

    # Optional updates
    if "crop_name" in data or "name" in data:
        name = (data.get("crop_name") or data.get("name") or "").strip()
        if not name:
            return (
                jsonify(
                    {
                        "error": "Validation Error",
                        "message": "crop_name cannot be empty.",
                    }
                ),
                400,
            )
        crop.crop_name = name

    if "category" in data:
        cat = data["category"].strip().lower()
        if cat not in ALLOWED_CROP_CATEGORIES:
            return (
                jsonify(
                    {
                        "error": "Validation Error",
                        "message": (
                            f"Invalid category '{cat}'. Allowed: "
                            f"{', '.join(ALLOWED_CROP_CATEGORIES)}"
                        ),
                    }
                ),
                400,
            )
        crop.category = cat

    if "unit" in data:
        unit = data["unit"].strip().lower()
        if unit not in ALLOWED_CROP_UNITS:
            return (
                jsonify(
                    {
                        "error": "Validation Error",
                        "message": f"Invalid unit '{unit}'. Allowed: {', '.join(ALLOWED_CROP_UNITS)}",
                    }
                ),
                400,
            )
        crop.unit = unit

    if "price_per_unit" in data or "price" in data:
        raw_price = data.get("price_per_unit") or data.get("price")
        try:
            price_val = Decimal(str(raw_price))
            if price_val <= 0:
                raise ValueError()
            crop.price_per_unit = price_val
        except (ValueError, TypeError):
            return (
                jsonify(
                    {
                        "error": "Validation Error",
                        "message": "price_per_unit must be a positive number greater than 0.",
                    }
                ),
                400,
            )

    if "quantity_available" in data or "quantity" in data:
        raw_qty = data.get("quantity_available") or data.get("quantity")
        try:
            qty_val = Decimal(str(raw_qty))
            if qty_val < 0:
                raise ValueError()
            crop.quantity_available = qty_val
            # Auto update status to sold_out if quantity becomes 0
            if qty_val == 0 and crop.status == "available":
                crop.status = "sold_out"
            elif qty_val > 0 and crop.status == "sold_out":
                crop.status = "available"
        except (ValueError, TypeError):
            return (
                jsonify(
                    {
                        "error": "Validation Error",
                        "message": "quantity_available cannot be negative.",
                    }
                ),
                400,
            )

    if "status" in data:
        status_val = data["status"].strip().lower()
        if status_val not in ALLOWED_CROP_STATUSES:
            return (
                jsonify(
                    {
                        "error": "Validation Error",
                        "message": (
                            f"Invalid status '{status_val}'. Allowed: "
                            f"{', '.join(ALLOWED_CROP_STATUSES)}"
                        ),
                    }
                ),
                400,
            )
        crop.status = status_val

    if "description" in data:
        crop.description = (data["description"] or "").strip() or None

    if "harvest_date" in data:
        hdate_str = (data["harvest_date"] or "").strip()
        if hdate_str:
            try:
                crop.harvest_date = datetime.strptime(hdate_str, "%Y-%m-%d").date()
            except ValueError:
                return (
                    jsonify(
                        {
                            "error": "Validation Error",
                            "message": "harvest_date must be in YYYY-MM-DD format.",
                        }
                    ),
                    400,
                )
        else:
            crop.harvest_date = None

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": f"Failed to update crop: {str(e)}",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "message": "Crop listing updated successfully.",
                "crop": crop.to_dict(include_farmer=True),
            }
        ),
        200,
    )


@marketplace_bp.route("/crops/<int:crop_id>", methods=["DELETE"])
@roles_required("farmer")
def delete_crop(crop_id):
    """
    DELETE /api/crops/<crop_id>
    (@login_required, role='farmer' or 'admin')
    Delist or soft-delete a crop by setting its status to 'archived'.
    Ensures foreign key relations with historical orders remain intact.
    """
    crop = db.session.get(Crop, crop_id)
    if not crop:
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": f"Crop with ID {crop_id} was not found.",
                }
            ),
            404,
        )

    current_user_id = session.get("user_id")
    current_role = session.get("role")
    if crop.farmer_id != current_user_id and current_role != "admin":
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "You do not have permission to delist this crop listing.",
                }
            ),
            403,
        )

    crop.status = "archived"
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": f"Failed to delist crop: {str(e)}",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "message": "Crop listing delisted and archived successfully.",
                "crop_id": crop_id,
            }
        ),
        200,
    )


# =============================================================================
# 2. ORDER PROCESSING ENDPOINTS (/api/orders)
# =============================================================================


@marketplace_bp.route("/orders", methods=["POST"])
@roles_required("buyer")
def place_order():
    """
    POST /api/orders
    (@login_required, role='buyer' or 'admin')
    Place a new order with atomic transactional integrity:
      - Validates shipping address and payment method.
      - Acquires row locks on requested crops.
      - Checks stock sufficiency.
      - Deducts quantity_available, updating crop status to 'sold_out' if 0.
      - Creates Order, OrderItem entries, Payment, and Delivery records.
      - Rolls back cleanly on any stock or database error.
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

    shipping_address = (data.get("shipping_address") or "").strip()
    payment_method_input = (data.get("payment_method") or "").strip().lower()
    items_data = data.get("items")

    # Normalize payment method aliases
    payment_method = "cash_on_delivery" if payment_method_input == "cod" else payment_method_input

    if not shipping_address:
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": "shipping_address is required.",
                }
            ),
            400,
        )

    if not payment_method or payment_method not in ALLOWED_PAYMENT_METHODS:
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": (
                        f"Invalid payment_method '{payment_method_input}'. Allowed: "
                        f"{', '.join(ALLOWED_PAYMENT_METHODS)}"
                    ),
                }
            ),
            400,
        )

    if not items_data or not isinstance(items_data, list):
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": "items must be a non-empty list of [{ crop_id, quantity }].",
                }
            ),
            400,
        )

    buyer_id = session["user_id"]
    total_amount = Decimal("0.00")
    order_items_to_persist = []
    farmer_locations = []

    try:
        # Atomic inventory check and lock
        for idx, item in enumerate(items_data):
            crop_id = item.get("crop_id")
            raw_quantity = item.get("quantity")

            if not crop_id or raw_quantity is None:
                db.session.rollback()
                return (
                    jsonify(
                        {
                            "error": "Validation Error",
                            "message": f"Item at index {idx} must include 'crop_id' and 'quantity'.",
                        }
                    ),
                    400,
                )

            try:
                qty_dec = Decimal(str(raw_quantity))
                if qty_dec <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                db.session.rollback()
                return (
                    jsonify(
                        {
                            "error": "Validation Error",
                            "message": f"Invalid quantity for crop_id {crop_id}. Must be greater than 0.",
                        }
                    ),
                    400,
                )

            # Query with lock
            crop = Crop.query.filter_by(crop_id=crop_id).with_for_update().first()
            if not crop:
                db.session.rollback()
                return (
                    jsonify(
                        {
                            "error": "Not Found",
                            "message": f"Crop with ID {crop_id} was not found.",
                        }
                    ),
                    404,
                )

            if crop.status != "available":
                db.session.rollback()
                return (
                    jsonify(
                        {
                            "error": "Bad Request",
                            "message": (
                                f"Crop '{crop.crop_name}' is currently {crop.status} "
                                f"and cannot be ordered."
                            ),
                        }
                    ),
                    400,
                )

            avail_dec = Decimal(str(crop.quantity_available))
            if avail_dec < qty_dec:
                db.session.rollback()
                return (
                    jsonify(
                        {
                            "error": "Conflict",
                            "message": (
                                f"Insufficient stock for '{crop.crop_name}'. "
                                f"Requested: {qty_dec} {crop.unit}, Available: {avail_dec} {crop.unit}."
                            ),
                        }
                    ),
                    400,
                )

            # Calculate item financial breakdown
            unit_price_dec = Decimal(str(crop.price_per_unit))
            subtotal_dec = (qty_dec * unit_price_dec).quantize(Decimal("0.01"))
            total_amount += subtotal_dec

            # Deduct inventory
            crop.quantity_available = avail_dec - qty_dec
            if crop.quantity_available == Decimal("0.00"):
                crop.status = "sold_out"

            order_items_to_persist.append(
                {
                    "crop": crop,
                    "quantity": qty_dec,
                    "unit_price": unit_price_dec,
                    "subtotal": subtotal_dec,
                }
            )

            # Record farmer pickup location
            if crop.farmer:
                addr_parts = [
                    crop.farmer.address_line,
                    crop.farmer.city,
                    crop.farmer.state,
                ]
                formatted_loc = ", ".join([p for p in addr_parts if p])
                if crop.farmer.postal_code:
                    formatted_loc += f" - {crop.farmer.postal_code}"
                if formatted_loc and formatted_loc not in farmer_locations:
                    farmer_locations.append(formatted_loc)

        # 1. Create Order record
        new_order = Order(
            buyer_id=buyer_id,
            total_amount=total_amount,
            shipping_address=shipping_address,
            status="placed",
            order_date=datetime.utcnow(),
        )
        db.session.add(new_order)
        db.session.flush()  # Generates order_id for foreign keys

        # 2. Create OrderItem records
        for item_info in order_items_to_persist:
            order_item = OrderItem(
                order_id=new_order.order_id,
                crop_id=item_info["crop"].crop_id,
                quantity=item_info["quantity"],
                unit_price=item_info["unit_price"],
                subtotal=item_info["subtotal"],
            )
            db.session.add(order_item)

        # 3. Create Payment record
        # Immediate payment completion simulated for UPI, Cards, NetBanking
        is_paid_now = payment_method in {"upi", "card", "netbanking", "mobile_money"}
        txn_ref = f"TXN-{payment_method.upper()}-{uuid.uuid4().hex[:10].upper()}"

        payment = Payment(
            order_id=new_order.order_id,
            amount=total_amount,
            payment_method=payment_method,
            status="completed" if is_paid_now else "pending",
            transaction_reference=txn_ref,
            paid_at=datetime.utcnow() if is_paid_now else None,
        )
        db.session.add(payment)

        # 4. Create Delivery record
        pickup_address_str = (
            " | ".join(farmer_locations)
            if farmer_locations
            else "Farmer Hub / Farm Gate"
        )
        tracking_num = f"TRK-{uuid.uuid4().hex[:12].upper()}"

        delivery = Delivery(
            order_id=new_order.order_id,
            transporter_id=None,
            pickup_address=pickup_address_str,
            delivery_address=shipping_address,
            tracking_number=tracking_num,
            status="pending",
        )
        db.session.add(delivery)

        # Commit entire atomic transaction
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": f"Transaction failed while processing order: {str(e)}",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "message": "Order placed successfully.",
                "order": new_order.to_dict(include_relations=True),
            }
        ),
        201,
    )


@marketplace_bp.route("/orders", methods=["GET"])
@login_required
def get_orders():
    """
    GET /api/orders
    (@login_required)
    Returns order list filtered by caller's role:
      - 'buyer': orders placed by this buyer.
      - 'farmer': orders containing crops posted by this farmer.
      - 'transporter': orders whose delivery is assigned to this transporter.
      - 'admin': all orders.
    """
    user_id = session.get("user_id")
    role = session.get("role")

    if role == "buyer":
        orders = (
            Order.query.filter_by(buyer_id=user_id)
            .order_by(Order.order_date.desc())
            .all()
        )
    elif role == "farmer":
        orders = (
            Order.query.join(OrderItem)
            .join(Crop)
            .filter(Crop.farmer_id == user_id)
            .distinct()
            .order_by(Order.order_date.desc())
            .all()
        )
    elif role == "transporter":
        orders = (
            Order.query.join(Delivery)
            .filter(Delivery.transporter_id == user_id)
            .distinct()
            .order_by(Order.order_date.desc())
            .all()
        )
    elif role == "admin":
        orders = Order.query.order_by(Order.order_date.desc()).all()
    else:
        orders = []

    return (
        jsonify(
            {
                "count": len(orders),
                "orders": [order.to_dict(include_relations=True) for order in orders],
            }
        ),
        200,
    )


@marketplace_bp.route("/orders/<int:order_id>", methods=["GET"])
@login_required
def get_order(order_id):
    """
    GET /api/orders/<order_id>
    (@login_required)
    Return complete order breakdown with items, payment, and delivery state.
    Enforces authorization: order buyer, participant farmer, assigned transporter, or admin.
    """
    order = db.session.get(Order, order_id)
    if not order:
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": f"Order with ID {order_id} was not found.",
                }
            ),
            404,
        )

    user_id = session.get("user_id")
    role = session.get("role")

    is_buyer = order.buyer_id == user_id
    is_farmer = any(
        item.crop and item.crop.farmer_id == user_id for item in order.items
    )
    is_transporter = (
        order.delivery and order.delivery.transporter_id == user_id
    )
    is_admin = role == "admin"

    if not (is_buyer or is_farmer or is_transporter or is_admin):
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "You do not have permission to view this order.",
                }
            ),
            403,
        )

    return jsonify({"order": order.to_dict(include_relations=True)}), 200


# =============================================================================
# 3. DELIVERY & TRANSPORTER ENDPOINTS (/api/deliveries)
# =============================================================================


@marketplace_bp.route("/deliveries", methods=["GET"])
@login_required
def get_deliveries():
    """
    GET /api/deliveries
    (@login_required)
    View deliveries filtered by role and optional status query params:
      - transporter: deliveries assigned to them, or unassigned/pending if requested
      - buyer: deliveries for orders placed by buyer
      - farmer: deliveries for orders involving farmer's crops
      - admin: all deliveries
    """
    user_id = session.get("user_id")
    role = session.get("role")

    status_filter = request.args.get("status")
    unassigned_filter = request.args.get("unassigned", "").lower() in ("true", "1")

    query = Delivery.query

    if role == "transporter":
        if unassigned_filter or status_filter == "pending":
            # Allow transporters to view pending jobs they can pick up
            query = query.filter(
                (Delivery.transporter_id == user_id) | (Delivery.transporter_id.is_(None))
            )
        else:
            # Default to deliveries assigned to this transporter
            query = query.filter(Delivery.transporter_id == user_id)
    elif role == "buyer":
        query = query.join(Order).filter(Order.buyer_id == user_id)
    elif role == "farmer":
        query = (
            query.join(Order)
            .join(OrderItem)
            .join(Crop)
            .filter(Crop.farmer_id == user_id)
            .distinct()
        )
    elif role == "admin":
        pass
    else:
        return jsonify({"count": 0, "deliveries": []}), 200

    if status_filter and status_filter.lower() != "all":
        query = query.filter(Delivery.status == status_filter.lower())

    deliveries = query.order_by(Delivery.created_at.desc()).all()

    return (
        jsonify(
            {
                "count": len(deliveries),
                "deliveries": [d.to_dict() for d in deliveries],
            }
        ),
        200,
    )


@marketplace_bp.route("/deliveries/<int:delivery_id>", methods=["GET"])
@login_required
def get_delivery(delivery_id):
    """
    GET /api/deliveries/<delivery_id>
    (@login_required)
    Retrieve single delivery details with tracking information.
    """
    delivery = db.session.get(Delivery, delivery_id)
    if not delivery:
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": f"Delivery with ID {delivery_id} was not found.",
                }
            ),
            404,
        )

    user_id = session.get("user_id")
    role = session.get("role")

    order = delivery.order
    is_transporter = delivery.transporter_id == user_id
    is_buyer = order and order.buyer_id == user_id
    is_farmer = order and any(
        item.crop and item.crop.farmer_id == user_id for item in order.items
    )
    is_admin = role == "admin"

    if not (is_transporter or is_buyer or is_farmer or is_admin):
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "You do not have permission to view this delivery.",
                }
            ),
            403,
        )

    return jsonify({"delivery": delivery.to_dict()}), 200


@marketplace_bp.route("/deliveries/<int:delivery_id>/status", methods=["PATCH"])
@login_required
def update_delivery_status(delivery_id):
    """
    PATCH /api/deliveries/<delivery_id>/status
    (@login_required)
    Update delivery status ('assigned', 'picked_up', 'in_transit', 'delivered', etc.).
    Transporters can claim an unassigned delivery or update their own assigned shipment.
    Cascades corresponding status updates to the associated Order.
    """
    delivery = db.session.get(Delivery, delivery_id)
    if not delivery:
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": f"Delivery with ID {delivery_id} was not found.",
                }
            ),
            404,
        )

    user_id = session.get("user_id")
    role = session.get("role")

    # Transporter or Admin permission check
    if role not in ("transporter", "admin"):
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "Only transporters or administrators can update delivery status.",
                }
            ),
            403,
        )

    data = request.get_json(silent=True)
    if not data or "status" not in data:
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "JSON body with 'status' field is required.",
                }
            ),
            400,
        )

    new_status = data["status"].strip().lower()
    if new_status not in ALLOWED_DELIVERY_STATUSES:
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": (
                        f"Invalid status '{new_status}'. Allowed: "
                        f"{', '.join(ALLOWED_DELIVERY_STATUSES)}"
                    ),
                }
            ),
            400,
        )

    # Transporter assignment rules
    if role == "transporter":
        if delivery.transporter_id is None:
            # Self-assign delivery when claiming
            delivery.transporter_id = user_id
        elif delivery.transporter_id != user_id:
            return (
                jsonify(
                    {
                        "error": "Forbidden",
                        "message": "You are not the assigned transporter for this delivery.",
                    }
                ),
                403,
            )

    delivery.status = new_status

    # Estimated delivery date if provided
    if "estimated_delivery" in data and data["estimated_delivery"]:
        try:
            delivery.estimated_delivery = datetime.fromisoformat(
                data["estimated_delivery"]
            )
        except ValueError:
            pass

    # Cascading status updates to associated Order
    order = delivery.order
    if new_status == "picked_up":
        if order and order.status in ("placed", "confirmed"):
            order.status = "processing"
    elif new_status == "in_transit":
        if order and order.status in ("placed", "confirmed", "processing"):
            order.status = "shipped"
    elif new_status == "delivered":
        delivery.actual_delivery = datetime.utcnow()
        if order:
            order.status = "delivered"
    elif new_status == "cancelled":
        if order:
            order.status = "cancelled"

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": f"Failed to update delivery status: {str(e)}",
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "message": f"Delivery status updated to '{new_status}'.",
                "delivery": delivery.to_dict(),
            }
        ),
        200,
    )
