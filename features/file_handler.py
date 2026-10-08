# File Handling and Serialization module
# Demonstrates: 'with' statement, os path operations, file.seek(), file.tell(), and pickle serialization
import os
import pickle
import logging
from datetime import datetime
from features import database

# Configure logger
logger = logging.getLogger("FileHandler")

# Resolve directories relative to the car_rental root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECEIPT_DIR = os.path.join(BASE_DIR, "receipts")
BACKUP_DIR = os.path.join(BASE_DIR, "backup")

# Ensure required folders exist
os.makedirs(RECEIPT_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)


def generate_receipt(bill):
    """
    Generates a text receipt file for a completed vehicle return.
    Uses os.path.exists() to check existence and 'with' statement to write data safely.
    Returns the generated receipt file path.
    """
    try:
        booking_id = bill["booking_id"]
        filename = f"receipt_{booking_id}.txt"
        os.makedirs(RECEIPT_DIR, exist_ok=True)
        file_path = os.path.join(RECEIPT_DIR, filename)

        # Check if receipt already exists (for syllabus demonstration)
        file_existed = os.path.exists(file_path)

        receipt_text = f"""==================================================
              CAR RENTAL RECEIPT
==================================================
Receipt Date   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Booking ID     : #{bill['booking_id']}
Customer Name  : {bill.get('customer_name', 'N/A')} (ID: {bill['customer_id']})
Vehicle        : {bill.get('vehicle_name', 'N/A')} [{bill.get('category', 'N/A')}]
Rate per Day   : Rs. {bill.get('rate_per_day', 0.0):.2f}
--------------------------------------------------
Rental Start   : {bill['start_date']}
Scheduled Due  : {bill['due_date']}
Actual Return  : {bill['return_date']}
Total Days Used: {bill['days_used']} day(s)
Overdue Days   : {bill['extra_days']} day(s)
--------------------------------------------------
Base Rent      : Rs. {bill['base_rent']:.2f}
Late Fee       : Rs. {bill['late_fee']:.2f}
--------------------------------------------------
TOTAL CHARGES  : Rs. {bill['total_amount']:.2f}
==================================================
          Thank you for choosing our service!
==================================================
"""
        # Write to file using 'with' statement for automatic resource cleanup
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(receipt_text)

        status_msg = "overwritten" if file_existed else "created"
        logger.info(f"Receipt #{booking_id} successfully {status_msg} at {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Error generating receipt for booking #{bill.get('booking_id')}: {str(e)}")
        raise


def read_receipt(booking_id):
    """
    Reads and returns the text content of a receipt by booking ID.
    Raises FileNotFoundError if receipt does not exist.
    """
    filename = f"receipt_{booking_id}.txt"
    file_path = os.path.join(RECEIPT_DIR, filename)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Receipt for Booking #{booking_id} not found at {file_path}")

    try:
        # Read file using 'with' statement
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"Error reading receipt #{booking_id}: {str(e)}")
        raise


def backup_data():
    """
    Fetches all vehicles, customers, and bookings from database,
    packs them into a dictionary, and serializes to backup/backup.pkl using pickle.dump.
    Returns the backup file path.
    """
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backup_file = os.path.join(BACKUP_DIR, "backup.pkl")

        # Gather plain data from database
        data = {
            "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "vehicles": database.get_all_vehicles(),
            "customers": database.get_all_customers(),
            "bookings": database.get_all_bookings()
        }

        # Write binary mode using 'with' and pickle.dump
        with open(backup_file, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"Database successfully backed up to {backup_file}")
        return backup_file

    except Exception as e:
        logger.error(f"Error creating pickle backup: {str(e)}")
        raise


def restore_preview():
    """
    Deserializes and returns the backup data dictionary using pickle.load (Read-only preview).
    Does NOT modify live database tables.
    """
    backup_file = os.path.join(BACKUP_DIR, "backup.pkl")

    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"Backup file not found at {backup_file}")

    try:
        # Read binary mode using 'with' and pickle.load
        with open(backup_file, "rb") as f:
            data = pickle.load(f)
        return data
    except Exception as e:
        logger.error(f"Error reading pickle backup: {str(e)}")
        raise


def get_backup_info():
    """
    Returns metadata about the backup file.
    Demonstrates syllabus topics: os.path.exists(), os.path.getsize(), file.seek(), and file.tell().
    """
    backup_file = os.path.join(BACKUP_DIR, "backup.pkl")

    if not os.path.exists(backup_file):
        return None

    try:
        os_size = os.path.getsize(backup_file)

        # Demonstrate syllabus topics: file.seek() and file.tell()
        with open(backup_file, "rb") as f:
            # Move file cursor to the end of file
            f.seek(0, os.SEEK_END)
            # tell() returns current cursor position (which equals file size in bytes)
            size_from_tell = f.tell()
            # Rewind cursor back to the beginning
            f.seek(0, os.SEEK_SET)

        mod_time = datetime.fromtimestamp(os.path.getmtime(backup_file)).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "path": backup_file,
            "size_bytes": size_from_tell,
            "size_kb": round(size_from_tell / 1024, 2),
            "last_modified": mod_time
        }
    except Exception as e:
        logger.error(f"Error getting backup info: {str(e)}")
        return None
