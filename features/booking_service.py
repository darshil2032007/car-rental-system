# Rental business service handling bookings, returns, and business logic
import logging
from datetime import date, datetime
from functools import wraps

from features.models import Vehicle, Hatchback, Sedan, SUV, Bike
from features.exceptions import VehicleNotAvailableError, CustomerNotFoundError, InvalidDatesError
from features import database

# Configure logger for audit trail (with console fallback if file is not writable)
logger = logging.getLogger("RentalService")
logger.setLevel(logging.INFO)
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    try:
        file_h = logging.FileHandler("rental.log")
        file_h.setFormatter(formatter)
        logger.addHandler(file_h)
    except Exception:
        # Fallback to console stream if rental.log cannot be created
        stream_h = logging.StreamHandler()
        stream_h.setFormatter(formatter)
        logger.addHandler(stream_h)


def log_action(func):
    """
    Decorator to log function execution and outcomes to rental.log.
    Helps in audit tracking and viva explanation of Python decorators.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            logger.info(f"SUCCESS: Executed '{func.__name__}' successfully.")
            return result
        except Exception as error:
            logger.error(f"FAILURE: '{func.__name__}' failed with error: {str(error)}")
            raise
    return wrapper


def build_vehicle_object(row):
    """
    Helper function to instantiate the correct Vehicle subclass
    (Hatchback, Sedan, SUV, Bike) based on the database category.
    Row structure: (vehicle_id, brand, model, category, rate_per_day, status)
    """
    v_id, brand, model, category, rate, status = row
    cat_lower = str(category).lower()

    if cat_lower == "hatchback":
        return Hatchback(v_id, brand, model, rate, status)
    elif cat_lower == "sedan":
        return Sedan(v_id, brand, model, rate, status)
    elif cat_lower == "suv":
        return SUV(v_id, brand, model, rate, status)
    elif cat_lower == "bike":
        return Bike(v_id, brand, model, rate, status)
    else:
        return Vehicle(v_id, brand, model, rate, category, status)


class RentalService:
    """
    Service class managing core rental operations.
    Encapsulates booking creation, vehicle returns, and querying.
    """

    @log_action
    def book_vehicle(self, customer_id, vehicle_id, start_date, due_date):
        """
        Validates dates, customer existence, and vehicle availability,
        then creates a booking and marks vehicle as Booked.
        """
        # Date parsing and validation
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, "%Y-%m-%d").date()

        if due_date < start_date:
            raise InvalidDatesError("Due date cannot be earlier than start date.")

        try:
            # Check customer existence
            customer = database.get_customer(customer_id)
            if not customer:
                raise CustomerNotFoundError(f"Customer with ID {customer_id} does not exist.")

            # Check vehicle existence and availability
            vehicle = database.get_vehicle(vehicle_id)
            if not vehicle:
                raise VehicleNotAvailableError(f"Vehicle with ID {vehicle_id} does not exist.")

            current_status = vehicle[5]
            if current_status != "Available":
                raise VehicleNotAvailableError(f"Vehicle '{vehicle[1]} {vehicle[2]}' is already {current_status}.")

            # Create booking and update status
            booking_id = database.add_booking(customer_id, vehicle_id, start_date, due_date)
            database.update_vehicle_status(vehicle_id, "Booked")
            return booking_id
        except Exception:
            raise

    @log_action
    def return_vehicle(self, booking_id, return_date):
        """
        Processes vehicle return, calculates rent using subclass multipliers,
        computes late fees (extra_days * rate * 1.5), closes booking,
        sets vehicle to Available, and returns billing summary dict.
        """
        if isinstance(return_date, str):
            return_date = datetime.strptime(return_date, "%Y-%m-%d").date()

        try:
            booking = database.get_booking(booking_id)
            if not booking:
                raise ValueError(f"Booking with ID {booking_id} does not exist.")

            # booking row:
            # 0: booking_id, 1: customer_id, 2: vehicle_id, 3: start_date, 4: due_date,
            # 5: return_date, 6: total_amount, 7: late_fee, 8: customer_name,
            # 9: brand, 10: model, 11: category, 12: rate_per_day
            if booking[5] is not None:
                raise ValueError(f"Booking #{booking_id} has already been closed on {booking[5]}.")

            start_date = booking[3]
            due_date = booking[4]
            vehicle_id = booking[2]

            if return_date < start_date:
                raise InvalidDatesError("Return date cannot be earlier than start date.")

            # Calculate rental days (minimum 1 day)
            days_used = (return_date - start_date).days
            if days_used <= 0:
                days_used = 1

            # Calculate overdue extra days
            extra_days = (return_date - due_date).days
            if extra_days < 0:
                extra_days = 0

            # Instantiate vehicle subclass to calculate base rent polymorphically
            vehicle_row = (vehicle_id, booking[9], booking[10], booking[11], booking[12], "Booked")
            vehicle_obj = build_vehicle_object(vehicle_row)
            base_rent = vehicle_obj.calculate_rent(days_used)

            # Late fee: extra_days * rate_per_day * 1.5
            late_fee = round(extra_days * float(vehicle_obj.rate_per_day) * 1.5, 2)
            total_amount = round(base_rent + late_fee, 2)

            # Close booking and mark vehicle Available
            database.close_booking(booking_id, return_date, total_amount, late_fee)
            database.update_vehicle_status(vehicle_id, "Available")

            return {
                "booking_id": booking_id,
                "customer_id": booking[1],
                "customer_name": booking[8],
                "vehicle_id": vehicle_id,
                "vehicle_name": f"{booking[9]} {booking[10]}",
                "category": booking[11],
                "rate_per_day": float(vehicle_obj.rate_per_day),
                "start_date": str(start_date),
                "due_date": str(due_date),
                "return_date": str(return_date),
                "days_used": days_used,
                "extra_days": extra_days,
                "base_rent": base_rent,
                "late_fee": late_fee,
                "total_amount": total_amount
            }
        except Exception:
            raise

    def get_available_vehicles(self, max_rate=None):
        """
        Returns available vehicles. Uses lambda with filter() to apply max_rate if specified.
        """
        vehicles = database.get_available_vehicles()
        if max_rate is not None and float(max_rate) > 0:
            # Using lambda and filter() to filter vehicles by rate_per_day (column index 4)
            vehicles = list(filter(lambda v: float(v[4]) <= float(max_rate), vehicles))
        return vehicles

    def get_overdue_bookings(self, today=None):
        """
        Generator function yielding overdue active bookings one by one.
        Active bookings have return_date as NULL and due_date earlier than today.
        """
        if today is None:
            today = date.today()
        elif isinstance(today, str):
            today = datetime.strptime(today, "%Y-%m-%d").date()

        all_bookings = database.get_all_bookings()
        for b in all_bookings:
            # b[5] is return_date. If None, the booking is active.
            if b[5] is None:
                due = b[4]
                if isinstance(due, str):
                    due = datetime.strptime(due, "%Y-%m-%d").date()
                if due < today:
                    yield b

    def get_vehicle_names(self, available_only=False):
        """
        Uses lambda with map() to return formatted 'ID: Brand Model (Category)' strings.
        Can optionally filter to available vehicles only.
        """
        vehicles = self.get_available_vehicles() if available_only else database.get_all_vehicles()
        # Using lambda and map()
        return list(map(lambda v: f"{v[0]}: {v[1]} {v[2]} ({v[3]})", vehicles))
