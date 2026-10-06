-- =====================================================================
-- FarmLink Database Seed Script (MySQL 8.0+)
-- Currency: Indian Rupees (INR / ₹)
-- =====================================================================

USE farmlink_db;

-- Disable foreign key checks during batch truncation/insertion if reloading
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE Deliveries;
TRUNCATE TABLE Payments;
TRUNCATE TABLE OrderItems;
TRUNCATE TABLE Orders;
TRUNCATE TABLE Crops;
TRUNCATE TABLE Users;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- 1. SEED USERS (13 entries: 1 Admin, 4 Farmers, 5 Buyers, 3 Transporters)
-- Passwords simulated using 9-character compact hash tokens: '$2a#...'
-- =====================================================================
INSERT INTO Users (
    user_id, full_name, email, phone_number, password_hash, role, status,
    address_line, city, state, postal_code, created_at
) VALUES
-- 1 System Admin
(1, 'Rajesh Sharma', 'admin@farmlink.in', '+919876543210', 
 '$2a#adm1n', 'admin', 'active',
 'Block C-4, Pragati Vihar', 'New Delhi', 'Delhi', '110003', '2026-08-01 09:00:00'),

-- 4 Farmers across India
(2, 'Gurpreet Singh', 'gurpreet.singh@kisanmail.in', '+919812345678', 
 '$2a#k1s02', 'farmer', 'active',
 'VPO Bhadson, Nabha Tehsil', 'Patiala', 'Punjab', '147202', '2026-08-05 10:15:00'),

(3, 'Ramesh Patil', 'ramesh.patil@kisanmail.in', '+919823456789', 
 '$2a#k1s03', 'farmer', 'active',
 'Gat No. 142, Pimpalgaon Baswant, Niphad', 'Nashik', 'Maharashtra', '422209', '2026-08-06 11:30:00'),

(4, 'Mallikarjun Gowda', 'malli.gowda@kisanmail.in', '+919834567890', 
 '$2a#k1s04', 'farmer', 'active',
 'Gram Panchayat Road, Holenarasipura', 'Hassan', 'Karnataka', '573211', '2026-08-07 08:45:00'),

(5, 'Murugan Selvam', 'murugan.selvam@kisanmail.in', '+919845678901', 
 '$2a#k1s05', 'farmer', 'active',
 'East Street, Alanganallur, Vadipatti', 'Madurai', 'Tamil Nadu', '625501', '2026-08-08 14:20:00'),

-- 5 Buyers across Indian commercial & residential hubs
(6, 'Amit Verma', 'amit.verma@freshmart.in', '+919856789012', 
 '$2a#buy06', 'buyer', 'active',
 'Flat 804, Tower 3, DLF Phase 4', 'Gurugram', 'Haryana', '122002', '2026-08-10 15:00:00'),

(7, 'Priya Kulkarni', 'priya.kulkarni@organicbites.co.in', '+919867890123', 
 '$2a#buy07', 'buyer', 'active',
 'Plot 18, Mayur Colony, Kothrud', 'Pune', 'Maharashtra', '411038', '2026-08-11 16:30:00'),

(8, 'Venkatesh Rao', 'venkat.rao@bengalurufresh.in', '+919878901234', 
 '$2a#buy08', 'buyer', 'active',
 '742, 100 Feet Road, HAL 2nd Stage, Indiranagar', 'Bengaluru', 'Karnataka', '560038', '2026-08-12 12:10:00'),

(9, 'Sunita Sundaram', 'sunita.sundaram@chennaideals.in', '+919889012345', 
 '$2a#buy09', 'buyer', 'active',
 'Old No. 45, New No. 22, Usman Road, T. Nagar', 'Chennai', 'Tamil Nadu', '600017', '2026-08-13 17:40:00'),

(10, 'Rohit Agarwal', 'rohit.agarwal@kiranamart.in', '+919890123456', 
 '$2a#buy10', 'buyer', 'active',
 'Sector V, Bidhannagar, Salt Lake', 'Kolkata', 'West Bengal', '700091', '2026-08-14 18:25:00'),

-- 3 Transporters / Fleet Drivers (Assigned to Deliveries)
(11, 'Jaswant Singh', 'jaswant.logistics@farmlink.in', '+919811122233', 
 '$2a#trn11', 'transporter', 'active',
 'Transport Nagar, GT Road', 'Ambala', 'Haryana', '133001', '2026-08-15 08:00:00'),

(12, 'Santosh Shinde', 'santosh.fleet@farmlink.in', '+919822233344', 
 '$2a#trn12', 'transporter', 'active',
 'Near APMC Yard, Sector 19, Vashi', 'Navi Mumbai', 'Maharashtra', '400703', '2026-08-15 09:30:00'),

(13, 'Manjunath K', 'manjunath.cargo@farmlink.in', '+919833344455', 
 '$2a#trn13', 'transporter', 'active',
 'Industrial Suburb, Stage 2, Yeshwanthpur', 'Bengaluru', 'Karnataka', '560022', '2026-08-16 10:15:00');

-- =====================================================================
-- 2. SEED CROPS (5 entries: Tomato, Onion, Basmati Rice, Ragi, Wheat)
-- Initial quantities: 200–500 kg each, pricing in ₹/kg
-- =====================================================================
INSERT INTO Crops (
    crop_id, farmer_id, crop_name, category, quantity_available, unit,
    price_per_unit, harvest_date, description, status, created_at
) VALUES
(1, 3, 'Tomato', 'vegetable', 450.00, 'kg', 
 30.00, '2026-09-15', 'Freshly harvested ripe hybrid red tomatoes from Nashik farms.', 'available', '2026-09-16 08:00:00'),

(2, 3, 'Onion', 'vegetable', 500.00, 'kg', 
 40.00, '2026-09-10', 'Grade-A Nashik pink onions, sun-cured with high shelf-life.', 'available', '2026-09-11 09:30:00'),

(3, 2, 'Basmati Rice', 'grain', 350.00, 'kg', 
 85.00, '2026-08-25', 'Traditional 1121 fragrant long-grain aged Basmati rice from Patiala.', 'available', '2026-08-28 10:00:00'),

(4, 4, 'Ragi', 'grain', 300.00, 'kg', 
 45.00, '2026-09-01', 'Organic finger millet (Ragi) rich in calcium and dietary fiber from Hassan.', 'available', '2026-09-03 11:15:00'),

(5, 2, 'Wheat', 'grain', 400.00, 'kg', 
 32.00, '2026-08-20', 'Premium Sharbati golden whole wheat grains, cleaned and graded.', 'available', '2026-08-22 07:45:00');

-- =====================================================================
-- 3. SEED ORDERS (12 entries: Placed by Buyers 6–10)
-- TotalAmount strictly matches sum of corresponding OrderItems
-- Statuses: placed, confirmed, shipped, delivered, cancelled
-- =====================================================================
INSERT INTO Orders (
    order_id, buyer_id, total_amount, shipping_address, status, order_date, created_at
) VALUES
-- Order 1: ₹3,150.00 (Delivered to Gurugram)
(1, 6, 3150.00, 'Flat 804, Tower 3, DLF Phase 4, Gurugram, Haryana - 122002', 
 'delivered', '2026-10-01 10:00:00', '2026-10-01 10:00:00'),

-- Order 2: ₹4,750.00 (Delivered to Pune)
(2, 7, 4750.00, 'Plot 18, Mayur Colony, Kothrud, Pune, Maharashtra - 411038', 
 'delivered', '2026-10-01 14:30:00', '2026-10-01 14:30:00'),

-- Order 3: ₹4,050.00 (Delivered to Bengaluru)
(3, 8, 4050.00, '742, 100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru, Karnataka - 560038', 
 'delivered', '2026-10-02 09:15:00', '2026-10-02 09:15:00'),

-- Order 4: ₹4,250.00 (Delivered to Chennai)
(4, 9, 4250.00, 'Old No. 45, New No. 22, Usman Road, T. Nagar, Chennai, Tamil Nadu - 600017', 
 'delivered', '2026-10-02 16:45:00', '2026-10-02 16:45:00'),

-- Order 5: ₹3,680.00 (Shipped to Kolkata)
(5, 10, 3680.00, 'Sector V, Bidhannagar, Salt Lake, Kolkata, West Bengal - 700091', 
 'shipped', '2026-10-03 11:20:00', '2026-10-03 11:20:00'),

-- Order 6: ₹3,500.00 (Shipped to Gurugram)
(6, 6, 3500.00, 'Flat 804, Tower 3, DLF Phase 4, Gurugram, Haryana - 122002', 
 'shipped', '2026-10-03 15:50:00', '2026-10-03 15:50:00'),

-- Order 7: ₹3,500.00 (Confirmed for Pune)
(7, 7, 3500.00, 'Plot 18, Mayur Colony, Kothrud, Pune, Maharashtra - 411038', 
 'confirmed', '2026-10-04 10:10:00', '2026-10-04 10:10:00'),

-- Order 8: ₹3,295.00 (Confirmed for Bengaluru)
(8, 8, 3295.00, '742, 100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru, Karnataka - 560038', 
 'confirmed', '2026-10-04 13:40:00', '2026-10-04 13:40:00'),

-- Order 9: ₹1,125.00 (Placed by Chennai)
(9, 9, 1125.00, 'Old No. 45, New No. 22, Usman Road, T. Nagar, Chennai, Tamil Nadu - 600017', 
 'placed', '2026-10-05 09:30:00', '2026-10-05 09:30:00'),

-- Order 10: ₹2,160.00 (Placed by Kolkata)
(10, 10, 2160.00, 'Sector V, Bidhannagar, Salt Lake, Kolkata, West Bengal - 700091', 
 'placed', '2026-10-05 14:15:00', '2026-10-05 14:15:00'),

-- Order 11: ₹2,050.00 (Cancelled by Gurugram)
(11, 6, 2050.00, 'Flat 804, Tower 3, DLF Phase 4, Gurugram, Haryana - 122002', 
 'cancelled', '2026-10-05 17:00:00', '2026-10-05 17:00:00'),

-- Order 12: ₹2,220.00 (Placed by Pune)
(12, 7, 2220.00, 'Plot 18, Mayur Colony, Kothrud, Pune, Maharashtra - 411038', 
 'placed', '2026-10-06 08:30:00', '2026-10-06 08:30:00');

-- =====================================================================
-- 4. SEED ORDER ITEMS (Between 1 and 4 items per order)
-- Crop 1: Tomato (₹30) | Crop 2: Onion (₹40) | Crop 3: Basmati (₹85)
-- Crop 4: Ragi (₹45)   | Crop 5: Wheat (₹32)
-- Subtotal = Quantity * UnitPrice
-- =====================================================================
INSERT INTO OrderItems (
    order_item_id, order_id, crop_id, quantity, unit_price, subtotal, created_at
) VALUES
-- Items for Order 1 (Total = ₹750 + ₹800 + ₹1600 = ₹3,150.00)
(1, 1, 1, 25.00, 30.00,  750.00, '2026-10-01 10:00:00'),
(2, 1, 2, 20.00, 40.00,  800.00, '2026-10-01 10:00:00'),
(3, 1, 5, 50.00, 32.00, 1600.00, '2026-10-01 10:00:00'),

-- Items for Order 2 (Total = ₹3400 + ₹1350 = ₹4,750.00)
(4, 2, 3, 40.00, 85.00, 3400.00, '2026-10-01 14:30:00'),
(5, 2, 4, 30.00, 45.00, 1350.00, '2026-10-01 14:30:00'),

-- Items for Order 3 (Total = ₹450 + ₹1000 + ₹1700 + ₹900 = ₹4,050.00)
(6, 3, 1, 15.00, 30.00,  450.00, '2026-10-02 09:15:00'),
(7, 3, 2, 25.00, 40.00, 1000.00, '2026-10-02 09:15:00'),
(8, 3, 3, 20.00, 85.00, 1700.00, '2026-10-02 09:15:00'),
(9, 3, 4, 20.00, 45.00,  900.00, '2026-10-02 09:15:00'),

-- Items for Order 4 (Total = ₹4,250.00)
(10, 4, 3, 50.00, 85.00, 4250.00, '2026-10-02 16:45:00'),

-- Items for Order 5 (Total = ₹2400 + ₹1280 = ₹3,680.00)
(11, 5, 2, 60.00, 40.00, 2400.00, '2026-10-03 11:20:00'),
(12, 5, 5, 40.00, 32.00, 1280.00, '2026-10-03 11:20:00'),

-- Items for Order 6 (Total = ₹900 + ₹1800 + ₹800 = ₹3,500.00)
(13, 6, 1, 30.00, 30.00,  900.00, '2026-10-03 15:50:00'),
(14, 6, 4, 40.00, 45.00, 1800.00, '2026-10-03 15:50:00'),
(15, 6, 5, 25.00, 32.00,  800.00, '2026-10-03 15:50:00'),

-- Items for Order 7 (Total = ₹1500 + ₹2000 = ₹3,500.00)
(16, 7, 1, 50.00, 30.00, 1500.00, '2026-10-04 10:10:00'),
(17, 7, 2, 50.00, 40.00, 2000.00, '2026-10-04 10:10:00'),

-- Items for Order 8 (Total = ₹1275 + ₹900 + ₹1120 = ₹3,295.00)
(18, 8, 3, 15.00, 85.00, 1275.00, '2026-10-04 13:40:00'),
(19, 8, 4, 20.00, 45.00,  900.00, '2026-10-04 13:40:00'),
(20, 8, 5, 35.00, 32.00, 1120.00, '2026-10-04 13:40:00'),

-- Items for Order 9 (Total = ₹1,125.00)
(21, 9, 4, 25.00, 45.00, 1125.00, '2026-10-05 09:30:00'),

-- Items for Order 10 (Total = ₹1200 + ₹960 = ₹2,160.00)
(22, 10, 1, 40.00, 30.00, 1200.00, '2026-10-05 14:15:00'),
(23, 10, 5, 30.00, 32.00,  960.00, '2026-10-05 14:15:00'),

-- Items for Order 11 (Total = ₹1200 + ₹850 = ₹2,050.00)
(24, 11, 2, 30.00, 40.00, 1200.00, '2026-10-05 17:00:00'),
(25, 11, 3, 10.00, 85.00,  850.00, '2026-10-05 17:00:00'),

-- Items for Order 12 (Total = ₹600 + ₹600 + ₹1020 = ₹2,220.00)
(26, 12, 1, 20.00, 30.00,  600.00, '2026-10-06 08:30:00'),
(27, 12, 2, 15.00, 40.00,  600.00, '2026-10-06 08:30:00'),
(28, 12, 3, 12.00, 85.00, 1020.00, '2026-10-06 08:30:00');

-- =====================================================================
-- 5. SEED PAYMENTS (12 entries: Matching Orders 1–12)
-- Simulated methods: UPI, NetBanking, Card, COD
-- Statuses: completed, pending, refunded, failed
-- =====================================================================
INSERT INTO Payments (
    payment_id, order_id, amount, payment_method, status,
    transaction_reference, paid_at, created_at
) VALUES
-- Order 1: ₹3,150.00 via UPI (Completed)
(1, 1, 3150.00, 'upi', 'completed', 
 'UPI-REF-20261001-984120', '2026-10-01 10:05:22', '2026-10-01 10:00:00'),

-- Order 2: ₹4,750.00 via NetBanking (Completed)
(2, 2, 4750.00, 'netbanking', 'completed', 
 'NB-HDFC-20261001-573190', '2026-10-01 14:35:10', '2026-10-01 14:30:00'),

-- Order 3: ₹4,050.00 via Card (Completed)
(3, 3, 4050.00, 'card', 'completed', 
 'CC-VISA-20261002-382104', '2026-10-02 09:20:45', '2026-10-02 09:15:00'),

-- Order 4: ₹4,250.00 via UPI (Completed)
(4, 4, 4250.00, 'upi', 'completed', 
 'UPI-REF-20261002-192847', '2026-10-02 16:50:18', '2026-10-02 16:45:00'),

-- Order 5: ₹3,680.00 via NetBanking (Completed)
(5, 5, 3680.00, 'netbanking', 'completed', 
 'NB-ICICI-20261003-462198', '2026-10-03 11:25:30', '2026-10-03 11:20:00'),

-- Order 6: ₹3,500.00 via Card (Completed)
(6, 6, 3500.00, 'card', 'completed', 
 'CC-MASTERCARD-20261003-772819', '2026-10-03 15:55:04', '2026-10-03 15:50:00'),

-- Order 7: ₹3,500.00 via UPI (Completed)
(7, 7, 3500.00, 'upi', 'completed', 
 'UPI-REF-20261004-918237', '2026-10-04 10:14:50', '2026-10-04 10:10:00'),

-- Order 8: ₹3,295.00 via NetBanking (Completed)
(8, 8, 3295.00, 'netbanking', 'completed', 
 'NB-SBI-20261004-639102', '2026-10-04 13:45:12', '2026-10-04 13:40:00'),

-- Order 9: ₹1,125.00 via Cash On Delivery (Pending upon delivery)
(9, 9, 1125.00, 'cod', 'pending', 
 'COD-TOKEN-20261005-001923', NULL, '2026-10-05 09:30:00'),

-- Order 10: ₹2,160.00 via UPI (Pending gateway verification)
(10, 10, 2160.00, 'upi', 'pending', 
 'UPI-REF-20261005-552190', NULL, '2026-10-05 14:15:00'),

-- Order 11: ₹2,050.00 via UPI (Refunded after order cancellation)
(11, 11, 2050.00, 'upi', 'refunded', 
 'UPI-REF-20261005-318924', '2026-10-05 17:05:00', '2026-10-05 17:00:00'),

-- Order 12: ₹2,220.00 via Card (Payment authorization failed)
(12, 12, 2220.00, 'card', 'failed', 
 'CC-VISA-20261006-829105', NULL, '2026-10-06 08:30:00');

-- =====================================================================
-- 6. SEED DELIVERIES (12 entries: Matching Orders 1–12)
-- Logistic couriers: Delhivery, Blue Dart, Ekart, Xpressbees, Shadowfax
-- Statuses: delivered, in_transit, assigned, picked_up, pending, cancelled
-- =====================================================================
INSERT INTO Deliveries (
    delivery_id, order_id, transporter_id, pickup_address, delivery_address,
    tracking_number, status, estimated_delivery, actual_delivery, created_at
) VALUES
-- Delivery 1 (Order 1 - Delivered via Jaswant Singh / Delhivery)
(1, 1, 11, 
 'Gat No. 142, Pimpalgaon Baswant, Niphad, Nashik, Maharashtra - 422209', 
 'Flat 804, Tower 3, DLF Phase 4, Gurugram, Haryana - 122002', 
 'DELHIVERY-IND-78291023', 'delivered', 
 '2026-10-04 18:00:00', '2026-10-03 16:45:00', '2026-10-01 11:00:00'),

-- Delivery 2 (Order 2 - Delivered via Santosh Shinde / Blue Dart)
(2, 2, 12, 
 'VPO Bhadson, Nabha Tehsil, Patiala, Punjab - 147202', 
 'Plot 18, Mayur Colony, Kothrud, Pune, Maharashtra - 411038', 
 'BLUEDART-IND-49201948', 'delivered', 
 '2026-10-04 14:00:00', '2026-10-04 13:20:00', '2026-10-01 15:30:00'),

-- Delivery 3 (Order 3 - Delivered via Manjunath K / Ekart)
(3, 3, 13, 
 'Gat No. 142, Pimpalgaon Baswant, Niphad, Nashik, Maharashtra - 422209', 
 '742, 100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru, Karnataka - 560038', 
 'EKART-IND-67192049', 'delivered', 
 '2026-10-05 17:00:00', '2026-10-05 15:10:00', '2026-10-02 10:30:00'),

-- Delivery 4 (Order 4 - Delivered via Jaswant Singh / Xpressbees)
(4, 4, 11, 
 'VPO Bhadson, Nabha Tehsil, Patiala, Punjab - 147202', 
 'Old No. 45, New No. 22, Usman Road, T. Nagar, Chennai, Tamil Nadu - 600017', 
 'XPRESSBEES-IND-81029384', 'delivered', 
 '2026-10-06 16:00:00', '2026-10-05 18:25:00', '2026-10-02 17:30:00'),

-- Delivery 5 (Order 5 - In Transit via Santosh Shinde / Shadowfax)
(5, 5, 12, 
 'Gat No. 142, Pimpalgaon Baswant, Niphad, Nashik, Maharashtra - 422209', 
 'Sector V, Bidhannagar, Salt Lake, Kolkata, West Bengal - 700091', 
 'SHADOWFAX-IND-92019482', 'in_transit', 
 '2026-10-08 19:00:00', NULL, '2026-10-03 12:00:00'),

-- Delivery 6 (Order 6 - In Transit via Manjunath K / Delhivery)
(6, 6, 13, 
 'Gram Panchayat Road, Holenarasipura, Hassan, Karnataka - 573211', 
 'Flat 804, Tower 3, DLF Phase 4, Gurugram, Haryana - 122002', 
 'DELHIVERY-IND-39104859', 'in_transit', 
 '2026-10-08 15:00:00', NULL, '2026-10-03 16:30:00'),

-- Delivery 7 (Order 7 - Assigned to Jaswant Singh / Blue Dart)
(7, 7, 11, 
 'Gat No. 142, Pimpalgaon Baswant, Niphad, Nashik, Maharashtra - 422209', 
 'Plot 18, Mayur Colony, Kothrud, Pune, Maharashtra - 411038', 
 'BLUEDART-IND-18294029', 'assigned', 
 '2026-10-09 18:00:00', NULL, '2026-10-04 11:00:00'),

-- Delivery 8 (Order 8 - Picked Up by Santosh Shinde / Ekart)
(8, 8, 12, 
 'VPO Bhadson, Nabha Tehsil, Patiala, Punjab - 147202', 
 '742, 100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru, Karnataka - 560038', 
 'EKART-IND-50192847', 'picked_up', 
 '2026-10-10 12:00:00', NULL, '2026-10-04 14:15:00'),

-- Delivery 9 (Order 9 - Assigned to Manjunath K / Xpressbees)
(9, 9, 13, 
 'Gram Panchayat Road, Holenarasipura, Hassan, Karnataka - 573211', 
 'Old No. 45, New No. 22, Usman Road, T. Nagar, Chennai, Tamil Nadu - 600017', 
 'XPRESSBEES-IND-30294819', 'assigned', 
 '2026-10-11 16:00:00', NULL, '2026-10-05 10:00:00'),

-- Delivery 10 (Order 10 - Pending courier assignment)
(10, 10, NULL, 
 'Gat No. 142, Pimpalgaon Baswant, Niphad, Nashik, Maharashtra - 422209', 
 'Sector V, Bidhannagar, Salt Lake, Kolkata, West Bengal - 700091', 
 'SHADOWFAX-IND-74829103', 'pending', 
 '2026-10-11 18:00:00', NULL, '2026-10-05 14:45:00'),

-- Delivery 11 (Order 11 - Cancelled before assignment)
(11, 11, NULL, 
 'Gat No. 142, Pimpalgaon Baswant, Niphad, Nashik, Maharashtra - 422209', 
 'Flat 804, Tower 3, DLF Phase 4, Gurugram, Haryana - 122002', 
 'DELHIVERY-IND-99918234', 'cancelled', 
 NULL, NULL, '2026-10-05 17:15:00'),

-- Delivery 12 (Order 12 - Pending courier assignment)
(12, 12, NULL, 
 'VPO Bhadson, Nabha Tehsil, Patiala, Punjab - 147202', 
 'Plot 18, Mayur Colony, Kothrud, Pune, Maharashtra - 411038', 
 'BLUEDART-IND-61928402', 'pending', 
 '2026-10-12 14:00:00', NULL, '2026-10-06 09:00:00');
