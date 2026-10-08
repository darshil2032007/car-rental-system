# OOP Models demonstrating Inheritance, Encapsulation, and Polymorphism

class Vehicle:
    """
    Base class representing a general vehicle.
    Demonstrates Encapsulation with a private __status attribute and getter/setter.
    """
    def __init__(self, vehicle_id, brand, model, rate_per_day, category="General", status="Available"):
        self.vehicle_id = vehicle_id
        self.brand = brand
        self.model = model
        self.rate_per_day = float(rate_per_day)
        self.category = category
        self.__status = status  # Private attribute for encapsulation

    # Getter for status
    @property
    def status(self):
        return self.__status

    # Setter for status
    @status.setter
    def status(self, new_status):
        allowed_statuses = ["Available", "Booked", "Maintenance"]
        if new_status in allowed_statuses:
            self.__status = new_status
        else:
            raise ValueError(f"Status must be one of {allowed_statuses}")

    # Base method to calculate rent
    def calculate_rent(self, days):
        """Calculates standard rent based on rate per day."""
        return days * self.rate_per_day

    def __str__(self):
        return f"[{self.category}] {self.brand} {self.model} - Rs.{self.rate_per_day}/day ({self.status})"


# Subclasses demonstrating Inheritance and Polymorphism (overriding calculate_rent)

class Hatchback(Vehicle):
    """Hatchback car with standard 1.0x rate multiplier."""
    def __init__(self, vehicle_id, brand, model, rate_per_day, status="Available"):
        super().__init__(vehicle_id, brand, model, rate_per_day, category="Hatchback", status=status)

    def calculate_rent(self, days):
        # 1.0x multiplier
        return round(days * self.rate_per_day * 1.0, 2)


class Sedan(Vehicle):
    """Sedan car with 1.2x comfort rate multiplier."""
    def __init__(self, vehicle_id, brand, model, rate_per_day, status="Available"):
        super().__init__(vehicle_id, brand, model, rate_per_day, category="Sedan", status=status)

    def calculate_rent(self, days):
        # 1.2x multiplier
        return round(days * self.rate_per_day * 1.2, 2)


class SUV(Vehicle):
    """SUV vehicle with 1.5x premium rate multiplier."""
    def __init__(self, vehicle_id, brand, model, rate_per_day, status="Available"):
        super().__init__(vehicle_id, brand, model, rate_per_day, category="SUV", status=status)

    def calculate_rent(self, days):
        # 1.5x multiplier
        return round(days * self.rate_per_day * 1.5, 2)


class Bike(Vehicle):
    """Two-wheeler motorbike with 0.8x economy rate multiplier."""
    def __init__(self, vehicle_id, brand, model, rate_per_day, status="Available"):
        super().__init__(vehicle_id, brand, model, rate_per_day, category="Bike", status=status)

    def calculate_rent(self, days):
        # 0.8x economy multiplier
        return round(days * self.rate_per_day * 0.8, 2)


class Customer:
    """Class representing a registered customer."""
    def __init__(self, customer_id, name, phone, email, license_no):
        self.customer_id = customer_id
        self.name = name
        self.phone = phone
        self.email = email
        self.license_no = license_no

    def __str__(self):
        return f"Customer #{self.customer_id}: {self.name} ({self.phone})"


class Booking:
    """Class representing a rental booking transaction."""
    def __init__(self, booking_id, customer_id, vehicle_id, start_date, due_date, return_date=None, total_amount=0.0, late_fee=0.0):
        self.booking_id = booking_id
        self.customer_id = customer_id
        self.vehicle_id = vehicle_id
        self.start_date = start_date
        self.due_date = due_date
        self.return_date = return_date
        self.total_amount = float(total_amount)
        self.late_fee = float(late_fee)

    def __str__(self):
        return f"Booking #{self.booking_id} (Customer: {self.customer_id}, Vehicle: {self.vehicle_id})"
