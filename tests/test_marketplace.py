import unittest
from datetime import datetime, date
from decimal import Decimal

from app import create_app
from models import db, User, Crop, Order, OrderItem, Payment, Delivery


class TestConfig:
    """Test configuration using in-memory SQLite database."""
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class MarketplaceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create all tables in memory
        db.create_all()

        # Seed test users: farmer, buyer, other_farmer, transporter
        self.farmer = User(
            full_name="Ramesh Patil",
            email="ramesh.farmer@farmlink.in",
            phone_number="+919823456789",
            role="farmer",
            status="active",
            address_line="Pimpalgaon Baswant",
            city="Nashik",
            state="Maharashtra",
            postal_code="422209",
        )
        self.farmer.set_password("farmer123")

        self.farmer2 = User(
            full_name="Gurpreet Singh",
            email="gurpreet@farmlink.in",
            phone_number="+919812345678",
            role="farmer",
            status="active",
            address_line="VPO Bhadson",
            city="Patiala",
            state="Punjab",
            postal_code="147202",
        )
        self.farmer2.set_password("farmer123")

        self.buyer = User(
            full_name="Priya Kulkarni",
            email="priya.buyer@farmlink.in",
            phone_number="+919867890123",
            role="buyer",
            status="active",
            address_line="Mayur Colony, Kothrud",
            city="Pune",
            state="Maharashtra",
            postal_code="411038",
        )
        self.buyer.set_password("buyer123")

        self.transporter = User(
            full_name="Santosh Shinde",
            email="santosh.trn@farmlink.in",
            phone_number="+919822233344",
            role="transporter",
            status="active",
            address_line="Sector 19, Vashi",
            city="Navi Mumbai",
            state="Maharashtra",
            postal_code="400703",
        )
        self.transporter.set_password("trans123")

        self.transporter2 = User(
            full_name="Jaswant Singh",
            email="jaswant.trn@farmlink.in",
            phone_number="+919811122233",
            role="transporter",
            status="active",
            address_line="Transport Nagar",
            city="Ambala",
            state="Haryana",
            postal_code="133001",
        )
        self.transporter2.set_password("trans123")

        self.admin = User(
            full_name="Rajesh Sharma",
            email="admin@farmlink.in",
            phone_number="+919876543210",
            role="admin",
            status="active",
            address_line="Pragati Vihar",
            city="New Delhi",
            state="Delhi",
            postal_code="110003",
        )
        self.admin.set_password("admin123")

        db.session.add_all([
            self.farmer,
            self.farmer2,
            self.buyer,
            self.transporter,
            self.transporter2,
            self.admin,
        ])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post(
            "/api/login",
            json={"email": email, "password": password},
        )

    # -------------------------------------------------------------------------
    # Crops Endpoint Tests
    # -------------------------------------------------------------------------

    def test_create_crop_as_farmer(self):
        self.login("ramesh.farmer@farmlink.in", "farmer123")
        payload = {
            "crop_name": "Organic Tomatoes",
            "category": "vegetable",
            "quantity_available": 100.0,
            "unit": "kg",
            "price_per_unit": 35.50,
            "harvest_date": "2026-10-15",
            "description": "Fresh vine-ripened organic tomatoes",
        }
        res = self.client.post("/api/crops", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["crop"]["crop_name"], "Organic Tomatoes")
        self.assertEqual(data["crop"]["farmer_id"], self.farmer.user_id)
        self.assertEqual(data["crop"]["quantity_available"], 100.0)
        self.assertEqual(data["crop"]["price_per_unit"], 35.50)
        self.assertEqual(data["crop"]["farmer_name"], "Ramesh Patil")

    def test_create_crop_rbac_enforcement(self):
        # Buyer cannot post crops
        self.login("priya.buyer@farmlink.in", "buyer123")
        payload = {
            "crop_name": "Apples",
            "quantity_available": 50,
            "price_per_unit": 80,
        }
        res = self.client.post("/api/crops", json=payload)
        self.assertEqual(res.status_code, 403)

        # Unauthenticated request fails
        self.client.post("/api/logout")
        res = self.client.post("/api/crops", json=payload)
        self.assertEqual(res.status_code, 401)

    def test_crop_validation_errors(self):
        self.login("ramesh.farmer@farmlink.in", "farmer123")
        # Missing required fields
        res = self.client.post("/api/crops", json={"crop_name": "Onions"})
        self.assertEqual(res.status_code, 400)

        # Negative price
        res = self.client.post(
            "/api/crops",
            json={
                "crop_name": "Onions",
                "quantity_available": 10,
                "price_per_unit": -20,
            },
        )
        self.assertEqual(res.status_code, 400)

        # Invalid category
        res = self.client.post(
            "/api/crops",
            json={
                "crop_name": "Onions",
                "quantity_available": 10,
                "price_per_unit": 20,
                "category": "invalid_cat",
            },
        )
        self.assertEqual(res.status_code, 400)

    def test_get_crops_and_filters(self):
        # Prepopulate crops
        c1 = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Hybrid Tomato",
            category="vegetable",
            quantity_available=200,
            unit="kg",
            price_per_unit=30.00,
            status="available",
        )
        c2 = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Pink Onion",
            category="vegetable",
            quantity_available=150,
            unit="kg",
            price_per_unit=45.00,
            status="available",
        )
        c3 = Crop(
            farmer_id=self.farmer2.user_id,
            crop_name="Basmati Rice",
            category="grain",
            quantity_available=300,
            unit="kg",
            price_per_unit=90.00,
            status="available",
        )
        c4 = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Archived Wheat",
            category="grain",
            quantity_available=50,
            unit="kg",
            price_per_unit=35.00,
            status="archived",
        )
        db.session.add_all([c1, c2, c3, c4])
        db.session.commit()

        # Default GET: returns all available crops (c1, c2, c3; excludes archived c4)
        res = self.client.get("/api/crops")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["count"], 3)

        # Category filter: 'grain'
        res = self.client.get("/api/crops?category=grain")
        data = res.get_json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["crops"][0]["crop_name"], "Basmati Rice")

        # Search filter: 'tomato'
        res = self.client.get("/api/crops?search=tomato")
        data = res.get_json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["crops"][0]["crop_name"], "Hybrid Tomato")

        # Price range filter: min_price=40, max_price=50
        res = self.client.get("/api/crops?min_price=40&max_price=50")
        data = res.get_json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["crops"][0]["crop_name"], "Pink Onion")

    def test_get_single_crop_details(self):
        c = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Golden Wheat",
            category="grain",
            quantity_available=500,
            unit="kg",
            price_per_unit=32.00,
            status="available",
        )
        db.session.add(c)
        db.session.commit()

        res = self.client.get(f"/api/crops/{c.crop_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["crop"]
        self.assertEqual(data["crop_name"], "Golden Wheat")
        self.assertEqual(data["farmer_name"], "Ramesh Patil")
        self.assertEqual(data["farmer_village"], "Pimpalgaon Baswant")
        self.assertEqual(data["farmer_state"], "Maharashtra")

    def test_update_crop_owner_only(self):
        c = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Red Chillies",
            category="vegetable",
            quantity_available=50,
            unit="kg",
            price_per_unit=120.00,
            status="available",
        )
        db.session.add(c)
        db.session.commit()

        # Farmer 2 tries to edit Farmer 1's crop -> 403 Forbidden
        self.login("gurpreet@farmlink.in", "farmer123")
        res = self.client.put(
            f"/api/crops/{c.crop_id}",
            json={"price_per_unit": 100.00},
        )
        self.assertEqual(res.status_code, 403)

        # Farmer 1 edits their own crop -> 200 OK
        self.login("ramesh.farmer@farmlink.in", "farmer123")
        res = self.client.put(
            f"/api/crops/{c.crop_id}",
            json={"price_per_unit": 110.00, "quantity_available": 40},
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["crop"]
        self.assertEqual(data["price_per_unit"], 110.00)
        self.assertEqual(data["quantity_available"], 40.0)

    def test_delete_crop_delist(self):
        c = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Seasonal Strawberries",
            category="fruit",
            quantity_available=30,
            unit="box",
            price_per_unit=250.00,
            status="available",
        )
        db.session.add(c)
        db.session.commit()

        self.login("ramesh.farmer@farmlink.in", "farmer123")
        res = self.client.delete(f"/api/crops/{c.crop_id}")
        self.assertEqual(res.status_code, 200)

        # Verify crop is archived
        archived_crop = db.session.get(Crop, c.crop_id)
        self.assertEqual(archived_crop.status, "archived")

        # It should no longer appear in default available listings
        get_res = self.client.get("/api/crops")
        self.assertEqual(get_res.get_json()["count"], 0)

    # -------------------------------------------------------------------------
    # Orders Endpoint Tests
    # -------------------------------------------------------------------------

    def test_place_order_success_with_inventory_deduction(self):
        # Setup crops
        c1 = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Fresh Carrots",
            category="vegetable",
            quantity_available=50.0,
            unit="kg",
            price_per_unit=40.00,
            status="available",
        )
        c2 = Crop(
            farmer_id=self.farmer2.user_id,
            crop_name="Premium Basmati",
            category="grain",
            quantity_available=20.0,
            unit="kg",
            price_per_unit=100.00,
            status="available",
        )
        db.session.add_all([c1, c2])
        db.session.commit()

        # Log in as buyer
        self.login("priya.buyer@farmlink.in", "buyer123")

        order_payload = {
            "shipping_address": "Plot 18, Mayur Colony, Kothrud, Pune - 411038",
            "payment_method": "upi",
            "items": [
                {"crop_id": c1.crop_id, "quantity": 20.0},  # 20 * 40 = 800
                {"crop_id": c2.crop_id, "quantity": 20.0},  # 20 * 100 = 2000 (buys all 20)
            ],
        }

        res = self.client.post("/api/orders", json=order_payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        order = data["order"]

        # Financial verification: 800 + 2000 = 2800
        self.assertEqual(order["total_amount"], 2800.00)
        self.assertEqual(order["status"], "placed")
        self.assertEqual(len(order["items"]), 2)

        # Payment verification
        self.assertIsNotNone(order["payment"])
        self.assertEqual(order["payment"]["amount"], 2800.00)
        self.assertEqual(order["payment"]["payment_method"], "upi")
        self.assertEqual(order["payment"]["status"], "completed")
        self.assertTrue(order["payment"]["transaction_reference"].startswith("TXN-UPI-"))

        # Delivery verification
        self.assertIsNotNone(order["delivery"])
        self.assertEqual(order["delivery"]["status"], "pending")
        self.assertTrue(order["delivery"]["tracking_number"].startswith("TRK-"))

        # Stock check in DB
        db_c1 = db.session.get(Crop, c1.crop_id)
        db_c2 = db.session.get(Crop, c2.crop_id)
        self.assertEqual(float(db_c1.quantity_available), 30.0)
        self.assertEqual(db_c1.status, "available")

        self.assertEqual(float(db_c2.quantity_available), 0.0)
        self.assertEqual(db_c2.status, "sold_out")

    def test_place_order_insufficient_stock_rollback(self):
        c = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Organic Spinach",
            category="vegetable",
            quantity_available=15.0,
            unit="kg",
            price_per_unit=25.00,
            status="available",
        )
        db.session.add(c)
        db.session.commit()

        self.login("priya.buyer@farmlink.in", "buyer123")
        # Attempt to order 20 kg when only 15 kg is available
        res = self.client.post(
            "/api/orders",
            json={
                "shipping_address": "Pune",
                "payment_method": "cod",
                "items": [{"crop_id": c.crop_id, "quantity": 20.0}],
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("Insufficient stock", res.get_json()["message"])

        # Verify stock was NOT modified
        db_c = db.session.get(Crop, c.crop_id)
        self.assertEqual(float(db_c.quantity_available), 15.0)
        self.assertEqual(db_c.status, "available")

        # Verify no orders created
        self.assertEqual(Order.query.count(), 0)

    def test_get_orders_role_isolation(self):
        c1 = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Guava",
            category="fruit",
            quantity_available=100.0,
            unit="kg",
            price_per_unit=50.00,
            status="available",
        )
        db.session.add(c1)
        db.session.commit()

        # Buyer places order
        self.login("priya.buyer@farmlink.in", "buyer123")
        res = self.client.post(
            "/api/orders",
            json={
                "shipping_address": "Pune",
                "payment_method": "upi",
                "items": [{"crop_id": c1.crop_id, "quantity": 10.0}],
            },
        )
        self.assertEqual(res.status_code, 201)
        order_id = res.get_json()["order"]["order_id"]

        # Buyer gets their orders
        res = self.client.get("/api/orders")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

        # Farmer 1 gets orders containing their crops
        self.login("ramesh.farmer@farmlink.in", "farmer123")
        res = self.client.get("/api/orders")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

        # Farmer 2 has no crops in this order -> count 0
        self.login("gurpreet@farmlink.in", "farmer123")
        res = self.client.get("/api/orders")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 0)

        # Farmer 2 cannot view order details directly -> 403 Forbidden
        res = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(res.status_code, 403)

        # Farmer 1 CAN view order details -> 200 OK
        self.login("ramesh.farmer@farmlink.in", "farmer123")
        res = self.client.get(f"/api/orders/{order_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["order"]["order_id"], order_id)

    # -------------------------------------------------------------------------
    # Deliveries Endpoint Tests
    # -------------------------------------------------------------------------

    def test_delivery_workflow_and_transporter_status_update(self):
        c = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Potatoes",
            category="vegetable",
            quantity_available=200.0,
            unit="kg",
            price_per_unit=25.00,
            status="available",
        )
        db.session.add(c)
        db.session.commit()

        # Buyer places order
        self.login("priya.buyer@farmlink.in", "buyer123")
        res = self.client.post(
            "/api/orders",
            json={
                "shipping_address": "Pune - 411038",
                "payment_method": "cash_on_delivery",
                "items": [{"crop_id": c.crop_id, "quantity": 50.0}],
            },
        )
        order_data = res.get_json()["order"]
        delivery_id = order_data["delivery"]["delivery_id"]
        order_id = order_data["order_id"]

        # Log in as transporter
        self.login("santosh.trn@farmlink.in", "trans123")

        # 1. Transporter views pending deliveries
        res = self.client.get("/api/deliveries?status=pending")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["count"], 1)

        # 2. Transporter claims delivery and marks as 'assigned'
        res = self.client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "assigned"},
        )
        self.assertEqual(res.status_code, 200)
        deliv = res.get_json()["delivery"]
        self.assertEqual(deliv["status"], "assigned")
        self.assertEqual(deliv["transporter_id"], self.transporter.user_id)

        # 3. Transporter updates status to 'in_transit' -> Order cascades to 'shipped'
        res = self.client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "in_transit"},
        )
        self.assertEqual(res.status_code, 200)
        db_order = db.session.get(Order, order_id)
        self.assertEqual(db_order.status, "shipped")

        # 4. Transporter updates status to 'delivered' -> Order cascades to 'delivered'
        res = self.client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "delivered"},
        )
        self.assertEqual(res.status_code, 200)
        deliv_final = res.get_json()["delivery"]
        self.assertEqual(deliv_final["status"], "delivered")
        self.assertIsNotNone(deliv_final["actual_delivery"])

        db_order = db.session.get(Order, order_id)
        self.assertEqual(db_order.status, "delivered")

    def test_not_found_endpoints(self):
        self.login("admin@farmlink.in", "admin123")
        # Non-existent crop
        res = self.client.get("/api/crops/99999")
        self.assertEqual(res.status_code, 404)

        # Non-existent order
        res = self.client.get("/api/orders/99999")
        self.assertEqual(res.status_code, 404)

        # Non-existent delivery
        res = self.client.get("/api/deliveries/99999")
        self.assertEqual(res.status_code, 404)

        # Update non-existent delivery
        res = self.client.patch("/api/deliveries/99999/status", json={"status": "in_transit"})
        self.assertEqual(res.status_code, 404)

    def test_delivery_invalid_status_and_forbidden_role(self):
        c = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Garlic",
            category="vegetable",
            quantity_available=100.0,
            unit="kg",
            price_per_unit=120.00,
            status="available",
        )
        db.session.add(c)
        db.session.commit()

        self.login("priya.buyer@farmlink.in", "buyer123")
        res = self.client.post(
            "/api/orders",
            json={
                "shipping_address": "Pune",
                "payment_method": "upi",
                "items": [{"crop_id": c.crop_id, "quantity": 10.0}],
            },
        )
        delivery_id = res.get_json()["order"]["delivery"]["delivery_id"]

        # Buyer attempts to patch delivery status -> 403 Forbidden
        res = self.client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "delivered"},
        )
        self.assertEqual(res.status_code, 403)

        # Transporter sends invalid status string -> 400 Validation Error
        self.login("santosh.trn@farmlink.in", "trans123")
        res = self.client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "unknown_status"},
        )
        self.assertEqual(res.status_code, 400)

    def test_transporter_conflict_other_transporter_assigned(self):
        c = Crop(
            farmer_id=self.farmer.user_id,
            crop_name="Ginger",
            category="vegetable",
            quantity_available=50.0,
            unit="kg",
            price_per_unit=80.00,
            status="available",
        )
        db.session.add(c)
        db.session.commit()

        self.login("priya.buyer@farmlink.in", "buyer123")
        res = self.client.post(
            "/api/orders",
            json={
                "shipping_address": "Pune",
                "payment_method": "upi",
                "items": [{"crop_id": c.crop_id, "quantity": 10.0}],
            },
        )
        delivery_id = res.get_json()["order"]["delivery"]["delivery_id"]

        # Transporter 1 claims delivery
        self.login("santosh.trn@farmlink.in", "trans123")
        res = self.client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "assigned"},
        )
        self.assertEqual(res.status_code, 200)

        # Transporter 2 tries to update Transporter 1's delivery -> 403 Forbidden
        self.login("jaswant.trn@farmlink.in", "trans123")
        res = self.client.patch(
            f"/api/deliveries/{delivery_id}/status",
            json={"status": "in_transit"},
        )
        self.assertEqual(res.status_code, 403)

    def test_admin_full_access(self):
        # Admin can view all crops, all orders, all deliveries
        self.login("admin@farmlink.in", "admin123")
        res = self.client.get("/api/orders")
        self.assertEqual(res.status_code, 200)
        res = self.client.get("/api/deliveries")
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()

