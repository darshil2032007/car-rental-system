# Database operations using mysql-connector-python with parameterized queries
import os
import mysql.connector

def _get_setting(key, default=""):
    """Reads setting from environment variable with fallback to Streamlit secrets."""
    val = os.getenv(key)
    if val is not None and str(val).strip() != "":
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default

# Database connection configuration from environment variables or Streamlit secrets
HOST = _get_setting("DB_HOST", "localhost")
PORT = int(_get_setting("DB_PORT", "3306"))
USER = _get_setting("DB_USER", "root")
PASSWORD = _get_setting("DB_PASSWORD", "")
DATABASE = _get_setting("DB_NAME", "car_rental_db")
DB_SSL = _get_setting("DB_SSL", "false").lower() == "true"


def get_connection(use_database=True):
    """
    Establishes and returns a connection to MySQL (supports local and cloud like Aiven).
    Passes port and optional SSL flag.
    """
    config = {
        "host": HOST,
        "port": PORT,
        "user": USER,
        "password": PASSWORD,
    }
    if use_database:
        config["database"] = DATABASE
    if DB_SSL:
        config["ssl_disabled"] = False

    return mysql.connector.connect(**config)


def create_tables():
    """
    Creates the database if missing and initializes vehicles, customers, and bookings tables.
    Gracefully handles cloud environments where CREATE DATABASE is restricted.
    """
    # Step 1: Attempt to create database if permitted (e.g. local MySQL)
    try:
        conn = get_connection(use_database=False)
        try:
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    except Exception:
        # On cloud databases (like Aiven), CREATE DATABASE is often restricted;
        # the database already exists or is pre-allocated.
        pass

    # Step 2: Create tables within the target database
    conn = get_connection(use_database=True)
    try:
        cursor = conn.cursor()

        # Vehicles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
                brand VARCHAR(50) NOT NULL,
                model VARCHAR(50) NOT NULL,
                category VARCHAR(20) NOT NULL,
                rate_per_day DECIMAL(10, 2) NOT NULL,
                status VARCHAR(20) DEFAULT 'Available'
            )
        """)

        # Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(15) NOT NULL,
                email VARCHAR(100) NOT NULL,
                license_no VARCHAR(20) NOT NULL UNIQUE
            )
        """)

        # Bookings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT NOT NULL,
                vehicle_id INT NOT NULL,
                start_date DATE NOT NULL,
                due_date DATE NOT NULL,
                return_date DATE NULL,
                total_amount DECIMAL(10, 2) DEFAULT 0.0,
                late_fee DECIMAL(10, 2) DEFAULT 0.0,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
            )
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# ---------------- VEHICLE OPERATIONS ----------------

def add_vehicle(brand, model, category, rate_per_day, status="Available"):
    """Inserts a new vehicle into the database."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO vehicles (brand, model, category, rate_per_day, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (brand, model, category, rate_per_day, status))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def get_all_vehicles():
    """Retrieves all vehicle records as a list of tuples."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT vehicle_id, brand, model, category, rate_per_day, status FROM vehicles")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_available_vehicles():
    """Retrieves only vehicles that are currently Available."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT vehicle_id, brand, model, category, rate_per_day, status FROM vehicles WHERE status = 'Available'")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_vehicle(vehicle_id):
    """Retrieves a single vehicle by ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT vehicle_id, brand, model, category, rate_per_day, status FROM vehicles WHERE vehicle_id = %s", (vehicle_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def update_vehicle_status(vehicle_id, status):
    """Updates the status of a vehicle (Available / Booked)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE vehicles SET status = %s WHERE vehicle_id = %s", (status, vehicle_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def update_vehicle_rate(vehicle_id, rate_per_day):
    """Updates the daily rental rate for a vehicle."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE vehicles SET rate_per_day = %s WHERE vehicle_id = %s", (rate_per_day, vehicle_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def delete_vehicle(vehicle_id):
    """Deletes a vehicle record by ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vehicles WHERE vehicle_id = %s", (vehicle_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# ---------------- CUSTOMER OPERATIONS ----------------

def add_customer(name, phone, email, license_no):
    """Registers a new customer and returns their customer_id."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO customers (name, phone, email, license_no)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (name, phone, email, license_no))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def get_customer(customer_id):
    """Retrieves a single customer by ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT customer_id, name, phone, email, license_no FROM customers WHERE customer_id = %s", (customer_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_all_customers():
    """Retrieves all registered customers."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT customer_id, name, phone, email, license_no FROM customers")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ---------------- BOOKING OPERATIONS ----------------

def add_booking(customer_id, vehicle_id, start_date, due_date):
    """Creates a new rental booking record."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO bookings (customer_id, vehicle_id, start_date, due_date)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (customer_id, vehicle_id, start_date, due_date))
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def get_booking(booking_id):
    """Retrieves a booking record along with customer and vehicle names."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT b.booking_id, b.customer_id, b.vehicle_id, b.start_date, b.due_date, 
                   b.return_date, b.total_amount, b.late_fee,
                   c.name, v.brand, v.model, v.category, v.rate_per_day
            FROM bookings b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            WHERE b.booking_id = %s
        """
        cursor.execute(query, (booking_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_all_bookings():
    """Retrieves all bookings with customer and vehicle details."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT b.booking_id, b.customer_id, b.vehicle_id, b.start_date, b.due_date, 
                   b.return_date, b.total_amount, b.late_fee,
                   c.name AS customer_name, v.brand, v.model, v.category
            FROM bookings b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            ORDER BY b.booking_id DESC
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def close_booking(booking_id, return_date, total_amount, late_fee):
    """Marks a booking as returned, saving return date and charges."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
            UPDATE bookings
            SET return_date = %s, total_amount = %s, late_fee = %s
            WHERE booking_id = %s
        """
        cursor.execute(query, (return_date, total_amount, late_fee, booking_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
