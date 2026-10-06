-- =====================================================================
-- FarmLink Database Schema (MySQL 8.0+)
-- =====================================================================

DROP DATABASE IF EXISTS farmlink_db;
CREATE DATABASE farmlink_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_0900_ai_ci;
USE farmlink_db;

-- ---------------------------------------------------------------------
-- Table: Users
-- Stores farmers, buyers, logistics transporters, and administrators
-- ---------------------------------------------------------------------
CREATE TABLE Users (
    user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('farmer', 'buyer', 'transporter', 'admin') NOT NULL DEFAULT 'buyer',
    status ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active',
    address_line TEXT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table: Crops
-- Stores crop listings posted by farmers
-- ---------------------------------------------------------------------
CREATE TABLE Crops (
    crop_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    farmer_id BIGINT UNSIGNED NOT NULL,
    crop_name VARCHAR(100) NOT NULL,
    category ENUM('grain', 'vegetable', 'fruit', 'pulse', 'oilseed', 'other') NOT NULL DEFAULT 'vegetable',
    quantity_available DECIMAL(10, 2) NOT NULL,
    unit ENUM('kg', 'ton', 'quintal', 'box', 'bag') NOT NULL DEFAULT 'kg',
    price_per_unit DECIMAL(10, 2) NOT NULL,
    harvest_date DATE NULL,
    description TEXT NULL,
    status ENUM('available', 'reserved', 'sold_out', 'archived') NOT NULL DEFAULT 'available',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_crops_quantity CHECK (quantity_available >= 0),
    CONSTRAINT chk_crops_price CHECK (price_per_unit > 0),
    CONSTRAINT fk_crops_farmer FOREIGN KEY (farmer_id)
        REFERENCES Users(user_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table: Orders
-- Stores purchase orders placed by buyers
-- ---------------------------------------------------------------------
CREATE TABLE Orders (
    order_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    buyer_id BIGINT UNSIGNED NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    shipping_address TEXT NOT NULL,
    status ENUM('pending', 'placed', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled') NOT NULL DEFAULT 'placed',
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_orders_total_amount CHECK (total_amount >= 0),
    CONSTRAINT fk_orders_buyer FOREIGN KEY (buyer_id)
        REFERENCES Users(user_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table: OrderItems
-- Junction table detailing items and quantities within an order
-- ---------------------------------------------------------------------
CREATE TABLE OrderItems (
    order_item_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    crop_id BIGINT UNSIGNED NOT NULL,
    quantity DECIMAL(10, 2) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_order_items_quantity CHECK (quantity > 0),
    CONSTRAINT chk_order_items_price CHECK (unit_price > 0),
    CONSTRAINT chk_order_items_subtotal CHECK (subtotal >= 0),
    CONSTRAINT uk_order_crop UNIQUE (order_id, crop_id),
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id)
        REFERENCES Orders(order_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_order_items_crop FOREIGN KEY (crop_id)
        REFERENCES Crops(crop_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table: Payments
-- Tracks payment transactions for orders
-- ---------------------------------------------------------------------
CREATE TABLE Payments (
    payment_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    payment_method ENUM('card', 'netbanking', 'bank_transfer', 'upi', 'mobile_money', 'cash_on_delivery', 'cod') NOT NULL,
    status ENUM('pending', 'completed', 'failed', 'refunded') NOT NULL DEFAULT 'pending',
    transaction_reference VARCHAR(100) NOT NULL UNIQUE,
    paid_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_payments_amount CHECK (amount > 0),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id)
        REFERENCES Orders(order_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table: Deliveries
-- Manages delivery fulfillment, shipment tracking, and transporter assignment
-- ---------------------------------------------------------------------
CREATE TABLE Deliveries (
    delivery_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL UNIQUE,
    transporter_id BIGINT UNSIGNED NULL,
    pickup_address TEXT NOT NULL,
    delivery_address TEXT NOT NULL,
    tracking_number VARCHAR(100) NOT NULL UNIQUE,
    status ENUM('pending', 'assigned', 'picked_up', 'in_transit', 'delivered', 'failed', 'cancelled') NOT NULL DEFAULT 'pending',
    estimated_delivery DATETIME NULL DEFAULT NULL,
    actual_delivery DATETIME NULL DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT fk_deliveries_order FOREIGN KEY (order_id)
        REFERENCES Orders(order_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_deliveries_transporter FOREIGN KEY (transporter_id)
        REFERENCES Users(user_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;
